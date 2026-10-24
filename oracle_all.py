import importlib.util, pathlib, sys, os
sys.path.insert(0, "ARC-AGI-3-Agents")
from arcengine import GameAction, ActionInput

# Test oracle on all 25 public games
env_dir = pathlib.Path("environment_files")
for game_dir in sorted(env_dir.iterdir()):
    for version_dir in game_dir.iterdir():
        py_files = list(version_dir.glob("*.py"))
        if not py_files:
            continue
        game_file = py_files[0]
        game_name = game_dir.name
        try:
            spec = importlib.util.spec_from_file_location(
                f"game_{game_name}", game_file
            )
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            
            # Find the game class
            game_cls = None
            for attr in dir(mod):
                obj = getattr(mod, attr)
                if (isinstance(obj, type) and 
                    hasattr(obj, 'step') and 
                    hasattr(obj, '_get_valid_actions') and
                    attr not in ('ARCBaseGame',)):
                    game_cls = obj
                    break
            
            if game_cls is None:
                print(f"{game_name}: no game class found")
                continue
                
            game = game_cls()
            va = game._get_valid_actions()
            action_ids = set()
            click_count = 0
            for a in va:
                aid = a.id.value if hasattr(a.id,'value') else int(a.id)
                action_ids.add(aid)
                if a.data:
                    click_count += 1
            print(f"{game_name}: actions={sorted(action_ids)}, "
                  f"valid_clicks={click_count}, "
                  f"total_valid={len(va)}")
        except Exception as e:
            print(f"{game_name}: ERROR {e}")
