import importlib.util, pathlib, sys
sys.path.insert(0, "ARC-AGI-3-Agents")
from arcengine import GameAction, GameState, ActionInput
game_path = pathlib.Path("environment_files/bp35/0a0ad940/bp35.py")
spec = importlib.util.spec_from_file_location("bp35_oracle", game_path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
game = module.Bp35()
inner = game.oztjzzyqoek
grid = inner.hdnrlfmyrj
player = inner.twdpowducb
px, py = player.qumspquyus
print(f"Player grid pos: {px},{py}  gravity_down={inner.vivnprldht}")
print("Below player:")
for dy in range(1,15):
    cy = py-dy
    tiles = [t.name for t in grid.jhzcxkveiw(px,cy)]
    print(f"  y={cy}: {tiles or 'empty'}")
print("Right of player:")
for dx in range(1,10):
    cx = px+dx
    tiles = [t.name for t in grid.jhzcxkveiw(cx,py)]
    below = [t.name for t in grid.jhzcxkveiw(cx,py-1)]
    print(f"  x={cx}: {tiles or 'empty'}, below={below or 'empty'}")
