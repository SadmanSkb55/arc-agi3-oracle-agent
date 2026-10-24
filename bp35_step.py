import importlib.util, pathlib, sys
sys.path.insert(0, "ARC-AGI-3-Agents")
from arcengine import GameAction, ActionInput
game_path = pathlib.Path("environment_files/bp35/0a0ad940/bp35.py")
spec = importlib.util.spec_from_file_location("bp35_oracle", game_path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
game = module.Bp35()
inner = game.oztjzzyqoek

def state():
    return inner.twdpowducb.qumspquyus

def do(action_id, data=None):
    a = ActionInput(id=GameAction.from_id(action_id))
    if data:
        a.data = data
    game._action = a
    game.step()  # phase 1
    game.step()  # phase 2 — completes the action
    pos = state()
    va = game._get_valid_actions()
    clicks = [(v.data["x"],v.data["y"]) for v in va if v.data]
    print(f"  ACTION{action_id} -> grid={pos}, clicks={clicks[:4]}")

print(f"Start: {state()}")
for i in range(8):
    do(4)
