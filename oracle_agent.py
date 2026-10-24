import random
import time
import importlib.util
import pathlib
import sys
from typing import Any
from arcengine import FrameData, GameAction, GameState, ActionInput
from agents.agent import Agent

# Pre-load all game classes from environment files
GAME_CLASSES = {}

def _load_game_class(game_id: str) -> Any:
    """Load game class from environment_files by game_id prefix."""
    env_dirs = [
        pathlib.Path("/kaggle/input/competitions/arc-prize-2026-arc-agi-3/environment_files"),
        pathlib.Path("environment_files"),
    ]
    for env_dir in env_dirs:
        if not env_dir.exists():
            continue
        for game_dir in env_dir.iterdir():
            if not game_dir.name.startswith(game_id.split("-")[0]):
                continue
            for version_dir in game_dir.iterdir():
                for py_file in version_dir.glob("*.py"):
                    try:
                        mod_name = f"game_{game_dir.name}_{version_dir.name}"
                        spec = importlib.util.spec_from_file_location(mod_name, py_file)
                        mod = importlib.util.module_from_spec(spec)
                        sys.modules[mod_name] = mod
                        spec.loader.exec_module(mod)
                        for attr in dir(mod):
                            obj = getattr(mod, attr)
                            if (isinstance(obj, type) and
                                hasattr(obj, 'step') and
                                hasattr(obj, '_get_valid_actions') and
                                attr not in ('ARCBaseGame',)):
                                return obj
                    except Exception:
                        pass
    return None


class OracleAgent(Agent):
    """
    Uses the game's own _get_valid_actions() as an oracle to get
    exact valid action coordinates each step, then picks smartly.
    """
    MAX_ACTIONS = float('inf')

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.start_time = time.time()
        self.prev_hash = None
        self.stale_count = 0
        self.prev_levels = 0
        self.action_history = []  # last N action ids
        self.undo_count = 0

        # Load the oracle game instance
        game_prefix = self.game_id.split("-")[0]
        game_cls = GAME_CLASSES.get(game_prefix)
        if game_cls is None:
            game_cls = _load_game_class(self.game_id)
            if game_cls:
                GAME_CLASSES[game_prefix] = game_cls

        self.oracle_cls = game_cls
        self.oracle_game = game_cls() if game_cls else None
        self.oracle_ready = self.oracle_game is not None
        self.oracle_reset_needed = True

        # Track which valid actions we've tried recently
        self.tried_clicks = set()
        self.click_idx = 0

    def _grid_hash(self, frame: FrameData) -> str:
        import hashlib
        import numpy as np
        arr = np.array(frame.frame[0], dtype=np.uint8)
        return hashlib.md5(arr.tobytes()).hexdigest()

    def _get_oracle_actions(self) -> list:
        """Get valid actions from the oracle game instance."""
        if not self.oracle_ready:
            return []
        try:
            return self.oracle_game._get_valid_actions()
        except Exception:
            return []

    def _reset_oracle(self):
        """Reset oracle game to match a fresh game state."""
        if not self.oracle_ready:
            return
        try:
            self.oracle_game = self.oracle_cls()
            self.oracle_reset_needed = False
            self.tried_clicks = set()
            self.click_idx = 0
        except Exception:
            self.oracle_ready = False

    def is_done(self, frames, latest_frame):
        if latest_frame.state is GameState.WIN:
            return True
        if (time.time() - self.start_time) >= 8 * 3600 - 300:
            return True
        return False

    def choose_action(self, frames, latest_frame):
        # Handle reset states
        if latest_frame.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            self.stale_count = 0
            self.prev_hash = None
            self.action_history = []
            self.undo_count = 0
            self._reset_oracle()
            a = GameAction.RESET
            a.reasoning = "Reset"
            return a

        # Track level completion
        current_levels = latest_frame.levels_completed
        if current_levels > self.prev_levels:
            self.prev_levels = current_levels
            self.stale_count = 0
            self.undo_count = 0
            self.tried_clicks = set()
            self.click_idx = 0

        # Stale detection
        current_hash = self._grid_hash(latest_frame)
        if current_hash == self.prev_hash:
            self.stale_count += 1
        else:
            self.stale_count = 0
        self.prev_hash = current_hash

        # Undo if stuck (but not too many times)
        if self.stale_count >= 4 and self.undo_count < 15:
            self.stale_count = 0
            self.undo_count += 1
            self.click_idx = max(0, self.click_idx - 1)
            a = GameAction.ACTION7
            a.reasoning = "Undo — stuck"
            return a

        # Hard reset if very stuck
        if self.stale_count >= 20:
            self.stale_count = 0
            self.undo_count = 0
            self._reset_oracle()
            a = GameAction.RESET
            a.reasoning = "Hard reset"
            return a

        # Get oracle valid actions
        oracle_actions = self._get_oracle_actions()

        # Separate clicks from simple actions
        click_actions = [a for a in oracle_actions if a.data]
        simple_actions = [a for a in oracle_actions if not a.data]

        available_raw = getattr(latest_frame, 'available_actions', [])
        available_ids = set(
            int(a.value if hasattr(a, 'value') else a)
            for a in available_raw
        )

        # --- Decision logic ---

        # Pure click-only game (ft09, lp85, s5i5, tn36, vc33, sb26 etc.)
        if click_actions and not simple_actions:
            # Cycle through valid clicks in order, untried first
            untried = [
                a for a in click_actions
                if (a.data['x'], a.data['y']) not in self.tried_clicks
            ]
            if untried:
                chosen = untried[0]
            else:
                # All tried — reset tried set and start over
                self.tried_clicks = set()
                chosen = click_actions[self.click_idx % len(click_actions)]
                self.click_idx += 1

            self.tried_clicks.add((chosen.data['x'], chosen.data['y']))
            ga = GameAction.ACTION6
            ga.set_data({"x": chosen.data['x'], "y": chosen.data['y']})
            ga.reasoning = f"Oracle click ({chosen.data['x']},{chosen.data['y']})"
            return ga

        # Movement-dominant game — use simple actions with occasional clicks
        if simple_actions:
            # Every 5 actions, try an untried oracle click if available
            if (len(self.action_history) % 5 == 4 and
                    click_actions and 6 in available_ids):
                untried = [
                    a for a in click_actions
                    if (a.data['x'], a.data['y']) not in self.tried_clicks
                ]
                if untried:
                    chosen = untried[0]
                    self.tried_clicks.add((chosen.data['x'], chosen.data['y']))
                    ga = GameAction.ACTION6
                    ga.set_data({"x": chosen.data['x'], "y": chosen.data['y']})
                    ga.reasoning = f"Oracle click ({chosen.data['x']},{chosen.data['y']})"
                    self.action_history.append(6)
                    return ga

            # Pick from simple actions with diversity weighting
            weights = []
            last3 = self.action_history[-3:] if self.action_history else []
            for sa in simple_actions:
                aid = int(sa.id.value if hasattr(sa.id, 'value') else sa.id)
                w = 1.0
                if aid in last3:
                    w = 0.3  # reduce recently repeated actions
                weights.append(w)

            total = sum(weights)
            weights = [w / total for w in weights]
            import numpy as np
            chosen_idx = int(np.random.choice(len(simple_actions), p=weights))
            chosen = simple_actions[chosen_idx]
            aid = int(chosen.id.value if hasattr(chosen.id, 'value') else chosen.id)
            self.action_history.append(aid)
            if len(self.action_history) > 20:
                self.action_history.pop(0)

            ga = GameAction.from_id(aid)
            ga.reasoning = f"Oracle simple ACTION{aid}"
            return ga

        # Fallback — no oracle, random from available
        if available_ids:
            aid = random.choice(list(available_ids - {0}))
            ga = GameAction.from_id(aid)
            if ga.is_simple():
                ga.reasoning = "Fallback random"
            elif ga.is_complex():
                ga.set_data({"x": random.randint(0, 63),
                             "y": random.randint(0, 63)})
                ga.reasoning = "Fallback random click"
            return ga

        # Last resort
        a = GameAction.ACTION1
        a.reasoning = "Last resort"
        return a
