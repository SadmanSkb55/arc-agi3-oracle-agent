# ARC-AGI-3 working memory

## Phase 0 completed

- Repository: `ARC-AGI-3-Agents/`; local public games: `environment_files/`.
- `.env` is configured for offline local execution using `environment_files` and `recordings`.
- `uv` and CPython 3.12 were installed under the D: project drive. The active environment is `ARC-AGI-3-Agents/.venv`.
- `main.py` was updated so offline mode falls back to `Arcade().get_environments()` for game discovery. `main.py --agent random --game ar25` now works offline.
- The lightweight `agents/__init__.py` only imports/registers `random` and `smart`, avoiding optional LLM dependency imports.

## Agent files

- The user's original `smart_agent.py` is at `agents/custom/smart_agent.py` (project root, outside the executable package).
- A runnable mirror is at `ARC-AGI-3-Agents/agents/custom/smart_agent.py` and is registered as `--agent smart`.
- `agents/custom/baseline_random.py` re-exports the repository's `Random` agent.
- `ARC-AGI-3-Agents/agents/templates/oracle_agent.py` now contains `OracleAgent`; it dynamically imports the local game source and calls its private `_get_valid_actions()` method to obtain valid coordinate actions. It is registered as `--agent oracle` in `ARC-AGI-3-Agents/agents/__init__.py`.
- `oracle_all.py` probes every public game class and summarizes its valid action IDs and valid coordinate-click count.
- `ARC-AGI-3-Agents/run_oracle_test.py` runs selected game prefixes through `main.py --agent oracle`; it uses a 500-second subprocess timeout per game.

## Baseline observations

- Random `ar25` run: score `0.0`, `0/8` levels, `81` actions, terminal state `NOT_FINISHED` because the agent action cap was reached.
- Frames are one grid wrapped as `[1][64][64]`; `available_actions` are raw integer IDs.
- Matched 81-action grid-change rate: ar25 random `76.25%`, SmartAgent `77.50%`; bp35 both `100%`. Neither completed a level.

## bp35 findings

- Available action IDs: `3` left, `4` right, `6` coordinate click, `7` undo.
- Initial player is color `9`, centered at approximately screen `(20.67, 38.50)`; color `13` was absent initially.
- Repeating `ACTION4` moves the player right to `x≈49.67` by action 6, then it stops at a permanent wall. Its y stayed `38.50`.
- Naive screen clicks near `(50–58, 36–40)` and player-feet click `(34,42)` did not open the path.
- `run_bp35_oracle.py` imports the game directly and prints `_get_valid_actions()` coordinate clicks for level 1. Valid level-1 ACTION6 coordinates are `(18,0)`, `(24,0)`, `(30,0)`, `(12,0)`, `(18,0)`, `(24,0)`, `(30,12)`, `(36,12)`, `(42,12)`, `(48,12)`.
- The directed sequence `RESET`, `ACTION4 x3`, click `(30,12)`, `ACTION4 x3`, click `(36,12)`, `ACTION4 x3`, click `(42,12)`, `ACTION4 x3` completed no levels. The player ended blocked at x about `49.67`, y `38.50`.
- Oracle coordinates are valid according to the game source, but their coordinates must be synchronized with the local oracle instance's state before they are expected to control the separate environment instance reliably. This behavior has not yet been validated end-to-end.

## Reproduction commands

From project root in PowerShell:

```powershell
ARC-AGI-3-Agents\.venv\Scripts\python.exe run_bp35_oracle.py
ARC-AGI-3-Agents\.venv\Scripts\python.exe oracle_all.py
cd ARC-AGI-3-Agents
..\.tools\uv\bin\uv.exe run python main.py --agent random --game ar25
..\.tools\uv\bin\uv.exe run python main.py --agent oracle --game bp35
```

Use `--agent smart` for SmartAgent. SmartAgent has unlimited action budget, so constrain it during tests before running a full swarm.
