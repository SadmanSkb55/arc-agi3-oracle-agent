# ARC-AGI-3 Oracle Agent

A training-free agent for ARC-AGI-3 that uses oracle-guided action pruning to
reduce the effective action space from up to 4,096 possible coordinate clicks
down to 2-256 targeted actions per step.

This is the code accompanying the paper submission to the ARC Prize 2026 Paper Track.

## Core Idea

Each ARC-AGI-3 game is defined by a Python source file that exposes a method
called `_get_valid_actions()`. This method returns the exact set of semantically
valid actions for the current game configuration. Instead of exploring the full
action space randomly, the Oracle Agent queries this method at each step and
restricts its choices to the returned valid actions only.

This reduces the mean effective action space from 2,258 (nominal) to 28 (pruned),
a reduction of 98.8%.

## Results

| Agent | ARC-AGI-3 Public Score |
|---|---|
| Random baseline | ~0.00% |
| Oracle Agent | 0.26% |

The Oracle Agent achieves a non-zero score with zero learned parameters and
no GPU requirement.

## Requirements

- Python 3.12
- arc-agi 0.9.8 (from competition wheels)
- numpy

No GPU required. Runs entirely on CPU.

## File Structure

```
arc-agi3-oracle-agent/
├── agents/
│   └── templates/
│       └── oracle_agent.py     # Main agent implementation
├── oracle_all.py               # Action space analysis across all 25 public games
├── oracle_test.py              # Local testing script
└── README.md
```

## How It Works

### Game Categories

After analyzing all 25 public games, we identified three structural categories:

**Click-only games** (8 games): only ACTION6 (coordinate click) is valid.
The agent cycles through all valid coordinates, prioritizing untried ones.

**Movement games** (6 games): directional actions ACTION1-4 are the primary
interface. The agent uses diversity-weighted sampling to avoid oscillation.

**Mixed games** (6 games): both movement and targeted clicks are required.
The agent alternates between movement and oracle-guided clicks every 5 steps.

### Stuck Detection

If the frame hash does not change for four consecutive steps, the agent issues
ACTION7 (undo) up to 15 times before issuing a hard reset. This prevents
wasting the action budget on locally non-productive moves.

## Running the Agent

This agent is designed to run inside the ARC-AGI-3 Kaggle competition environment.
To run it locally against public games:

```bash
# Clone the ARC-AGI-3-Agents repo
git clone https://github.com/arcprize/ARC-AGI-3-Agents

# Install dependencies from competition wheels
pip install --find-links arc_agi_3_wheels arc-agi python-dotenv

# Register the oracle agent in agents/__init__.py
# Copy oracle_agent.py to ARC-AGI-3-Agents/agents/templates/

# Run against a public game
python main.py --agent oracle --game ft09
```

## Action Space Analysis

Run `oracle_all.py` to reproduce the action space reduction table from the paper:

```bash
python oracle_all.py
```

Output shows valid action counts per game before and after oracle pruning.

## Kaggle Submission

The Kaggle notebook for this submission is publicly available at:
[link to your Kaggle notebook]

## Paper

This code accompanies the paper submitted to the ARC Prize 2026 Paper Track:

"Oracle-Guided Action Pruning for Interactive Reasoning Agents: A Study on ARC-AGI-3"

Submitted to: https://www.kaggle.com/competitions/arc-prize-2026-paper-track

## Citation

If you use this work, please cite:

```
@misc{arc-agi3-oracle-agent-2026,
  author = {Sadman Islam},
  title = {Oracle-Guided Action Pruning for Interactive Reasoning Agents: A Study on ARC-AGI-3},
  year = {2026},
  publisher = {Kaggle},
  howpublished = {ARC Prize 2026 Paper Track},
  url = {https://www.kaggle.com/competitions/arc-prize-2026-paper-track}
}
```

## License

Apache 2.0
