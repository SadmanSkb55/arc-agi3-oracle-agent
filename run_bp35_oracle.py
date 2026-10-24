import importlib.util
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "ARC-AGI-3-Agents"))

game_path = pathlib.Path(__file__).parent / "environment_files" / "bp35" / "0a0ad940" / "bp35.py"
spec = importlib.util.spec_from_file_location("bp35_oracle", game_path)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load {game_path}")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

game = module.Bp35()
valid_actions = game._get_valid_actions()

print("Valid ACTION6 coordinates for bp35 level 1:")
for action in valid_actions:
    if action.data:
        print(f"x={action.data['x']}, y={action.data['y']}")
