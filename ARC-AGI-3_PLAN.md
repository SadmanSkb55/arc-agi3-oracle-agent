# ARC-AGI-3 — Execution Plan

**Win condition (ranked):**
1. A working, open-sourced agent that scores meaningfully above random on the public/private leaderboard.
2. A clean, honest paper documenting it (target 4.5/5, but a solid submitted paper beats an unfinished "perfect" one).
3. Prize/leaderboard placement — stretch goal, not the blocker for 1 and 2.

**Hard deadlines**
| Date | Event |
|---|---|
| Oct 26, 2026 | Entry deadline + Team merger deadline |
| Nov 2, 2026 | Final Submission deadline (AGI-3) |
| Nov 9, 2026 | Paper Track final submission |

**Golden rule:** never let an unfinished stretch feature (Phase 2/4 extras) block a working submission. Ship the safe version first, improve after.

---

## 0. Two Separate Environments — don't conflate them

| | Local | Kaggle |
|---|---|---|
| Purpose | Dev, iteration, ablations, debugging | **Official scored submission only** |
| Data | Practice API (arcprize.org) + 25 public game files | Private 110-game eval set (never seen locally) |
| Counts toward leaderboard? | **No** | **Yes — this is the only place that counts** |
| Compute | Your machine | Kaggle-hosted (CPU or L4x4/RTX, 9hr limit, no internet during run) |

You develop and prove the agent locally, then port the final, frozen agent code into a Kaggle Notebook and run it there to generate the real submission. A local run never produces a leaderboard entry — don't skip the Kaggle step thinking local testing is enough.

---

## 1. File Structure (target state)

```
arc-agi-3/
├── ARC-AGI-3-Agents/              # cloned repo (provided)
│   ├── agents/
│   │   ├── <existing template classes from repo — inspect before writing anything>
│   │   └── custom/
│   │       ├── __init__.py
│   │       ├── baseline_random.py     # Phase 0
│   │       ├── frame_diff_tracker.py  # Phase 1
│   │       ├── stuck_detector.py      # Phase 1
│   │       ├── novelty_explorer.py    # Phase 1
│   │       ├── object_targeter.py     # Phase 1 (ACTION6 coord targeting)
│   │       ├── transition_cache.py    # Phase 2 (cut first if behind)
│   │       └── full_agent.py          # combines modules, THE submission agent
│   ├── tests/
│   ├── main.py
│   ├── .env                       # local secrets — copy from .env.example, fill in real values, gitignored
│   ├── pyproject.toml
│   └── uv.lock
├── environment_files/             # 25 public games (provided)
├── notebooks/
│   └── kaggle_submission.ipynb    # mirrors full_agent.py, this is what runs on Kaggle
├── experiments/
│   ├── logs/                      # raw per-run logs, one file per config per game
│   └── ablation_results.csv       # Phase 3 output — this is your paper's evidence table
└── paper/
    ├── draft.md
    └── figures/                   # ablation plots, exported from ablation_results.csv
```

Build this by cloning the repo as-is and adding only the `custom/` folder and the three top-level dirs (`notebooks/`, `experiments/`, `paper/`). Don't restructure the existing repo — it's built to work with `main.py` and the `Swarm` class as shipped.

---

## 2. Environment & Dependencies

### Local
- **Python**: match whatever is pinned in `ARC-AGI-3-Agents/.python-version` — check it, don't assume.
- **uv** (the repo ships `pyproject.toml` + `uv.lock`, meaning it's uv-managed) — `uv sync` to install locked deps instead of raw pip, to avoid dependency drift from what the repo authors tested.
- **git**
- Additional libs not in the base repo you'll need to add for the agent logic:
  - `numpy`
  - `scipy` (specifically `scipy.ndimage.label` for connected-component segmentation — this is what drives object-aware ACTION6 targeting)
  - `python-dotenv` (only if `main.py` doesn't already load `.env` itself — check first, repo may already handle this)
- **Credentials**: `ARC-AGI-3-Agents/.env.example` lists the exact environment variables the repo expects (likely an API key and possibly a game/scorecard identifier, but copy the real names from that file — don't guess them). You'll need an API key from arcprize.org to hit the practice API locally.

### Kaggle
- Standard Kaggle Python environment already has `numpy`/`scipy` — no extra pip installs should be needed if you keep the agent dependency-light (recommended: don't add anything exotic).
- **No internet access during scored runs** — this is a hard rule in the competition rules, not optional. Any approach that calls an external API or downloads a model at runtime will fail the submission.
- GPU: you almost certainly don't need the L4x4/RTX pool for this plan — nothing here trains or runs a neural model. CPU runtime should be enough. Only reconsider GPU if you deliberately add a local open-weight model for reasoning (optional, cut first under time pressure — see fallbacks).
- Submission limit: 1 per day, up to 2 Final Submissions selected for scoring.

---

## 3. Phase-by-Phase

### Phase 0 — Today: Local setup + understand the interface
**Where:** Local
- Clone `ARC-AGI-3-Agents`, `uv sync`.
- Fill in `.env` from `.env.example` with your real API key.
- Run `main.py` against **one** public game from `environment_files/`. Inspect the raw frame JSON structure, confirm action space, confirm what a WIN/GAME_OVER state looks like.
- Read `agents/` — find the base `Agent` class (`is_done`, `choose_action`) and how `Swarm` dispatches across games. Do not write custom code until you've actually seen this, the repo's existing scaffolding may already handle things you'd otherwise rebuild.
- Write `baseline_random.py`: RESET + uniform-random valid action every step. This is your floor.

**Exit condition:** you've seen real frame data for at least one game and have a trivial agent running locally end to end.

---

### Phase 1 — Day 1: First real Kaggle submission (lock entry for real)
**Where:** Kaggle
- Port `baseline_random.py` into `notebooks/kaggle_submission.ipynb` as-is.
- Run it on Kaggle. This is what actually generates a scored submission and a submission ID — a local run does not count. Do this on day 1, not day 8, so you have a working submission pipeline locked in well before the Oct 26 entry deadline, with time to fix any Kaggle-specific friction (packaging, runtime limits, notebook environment quirks).
- **Fallback:** if the notebook pipeline has any friction (file paths, auth, runtime config), resolve it now while the agent itself is trivial — debugging a packaging issue is much harder once the agent logic is also complex.

**Exit condition:** one real, scored Kaggle submission exists, however low the score.

---

### Phase 2 — Day 1–4: Core agent logic (local dev)
**Where:** Local, build and test against the 25 public games

Build in this order, test each module in isolation before combining:
1. `frame_diff_tracker.py` — store last N frames per game, diff grids cell-by-cell after each action. This gives you, per game, an empirical table of "what did taking ACTION_k just change."
2. `stuck_detector.py` — if the last K actions produced zero grid change, force a RESET or force a different action family.
3. `novelty_explorer.py` — hash grid states (full grid hash, or a coarser feature like color histogram + connected-component count if full-grid hashing is too sparse to ever repeat), bias action selection toward state/action pairs seen least.
4. `object_targeter.py` — for ACTION6 (the coordinate action), don't sample (x, y) uniformly. Run `scipy.ndimage.label` on the grid to find connected components, sample coordinates at their centroids/boundaries instead.

This stack is also your paper's theory section: optimism-under-uncertainty exploration + object-aware targeting reduces the action budget vs. naive search — a claim you can actually back with the ablation table from Phase 4.

**Fallback if `object_targeter.py` doesn't beat random sampling on early tests:** fall back to coarse fixed-grid coordinate sampling (e.g. an 8×8 lattice of candidate points) instead of full connected-component segmentation — still non-uniform, much simpler, and cheap to implement if segmentation isn't paying off.

**Fallback if `novelty_explorer.py` state hashing is too sparse/slow to be useful:** fall back to simple epsilon-greedy with enforced action-type diversity (don't repeat the same action more than M times in a row) instead of full count-based curiosity.

---

### Phase 3 — Day 4–6: Efficiency layer
**Where:** Local
- Once a level's WIN signal fires, stop taking further actions immediately — the efficiency score is `min(human/agent, 1)²`, so wasted post-win actions are costly.
- `transition_cache.py`: once you've empirically learned "action X from state-pattern Y → effect Z" within a game, reuse it instead of re-exploring on repeated sub-patterns.

**Fallback — cut this module first if you're behind schedule.** A working agent without the cache is still a complete, honest submission. The cache is a score optimization, not a correctness requirement. Don't let it block Phase 4/5.

**Explicitly out of scope unless far ahead of schedule:** any local open-weight model for higher-level reasoning. No internet during scored runs means any such model must be bundled and loaded entirely offline inside the Kaggle notebook — real added complexity and risk for marginal gain this late in the cycle. If you do attempt it, it's the first thing to cut if it jeopardizes the Nov 2 deadline, and don't claim it in the paper abstract unless it's actually in your final submitted agent.

---

### Phase 4 — Day 6–8: Validate on all 25 public games, build the ablation table
**Where:** Local
- Run each config against all 25 public games, log completion % and action-efficiency ratio per game to `experiments/logs/`.
- Build `experiments/ablation_results.csv` with rows for:
  - Random baseline
  - + novelty exploration
  - + object-aware targeting
  - + transition cache (if kept)
- Pick whichever combination has the best average score across public games as your submission config.

**Fallback if full 25-game validation doesn't fit the time budget:** run on a representative subset (e.g. 10 games spanning different mechanics) and say so explicitly in the paper as a stated limitation — do not present subset results as if they were the full set.

---

### Phase 5 — Day 8–9 (before Oct 26): Final pre-deadline submissions
**Where:** Kaggle
- Port the finished `full_agent.py` into `kaggle_submission.ipynb`.
- Submit two configs as your two allowed Final Submissions:
  - **Safe**: stuck-detector + novelty exploration only (simpler, lower variance).
  - **Aggressive**: full pipeline including object targeting (+ cache if kept).
  - This way a bug in the aggressive version doesn't zero out your entry.

---

### Phase 6 — Day 9–16 (until Nov 2): Watch leaderboard, iterate
**Where:** Kaggle (submissions) + Local (fixes)
- Watch Public Leaderboard score as feedback.
- Any further tuning happens locally against public games, then gets re-submitted to Kaggle (1/day limit — plan submissions, don't burn them on untested changes).
- Final submission locked by **Nov 2**.

---

### Phase 7 — parallel from Day 4, finish by Nov 9: The paper
**Where:** Local (writing)
Map directly onto the 6 judged criteria:
- **Accuracy** → your actual leaderboard score + submission ID. Report the real number, not a projected one.
- **Theory** → the optimism/novelty-exploration argument for why fewer actions = more information-efficient exploration.
- **Completeness** → the full ablation table from Phase 4.
- **Novelty** → object-aware ACTION6 targeting via connected components, if it holds up in your ablations — check the competition forum once you're entered, in case this is already common practice, and adjust the novelty claim honestly either way.
- **Universality** → frame the exploration+targeting approach as applicable to any sparse-reward, partially-observed interactive RL setting, not just this benchmark.
- **Clarity** → ≤1,500 words, lead with the ablation table, don't pad.

**Non-negotiable:** every number in the paper comes from an actual logged run in `experiments/`. Do not estimate or round up results for the writeup.

---

## 4. Progress Tracker

- [ ] Phase 0 — local setup, baseline running locally
- [ ] Phase 1 — first real Kaggle submission (entry locked for real)
- [ ] Phase 2 — diff tracker / stuck detector / novelty / object targeting built
- [ ] Phase 3 — efficiency layer (or explicitly cut)
- [ ] Phase 4 — full ablation table built
- [ ] Phase 5 — two final submissions locked before Oct 26
- [ ] Phase 6 — iterating until Nov 2
- [ ] Phase 7 — paper drafted, submitted by Nov 9









###############################Revised 
Revised strategy

The Stochastic Goose CNN approach (learn which actions change frames) is actually the right foundation — but we need two improvements:

1. For ar25 (mirror puzzle):

ACTION6 must target visible sprites, not random coordinates. The game’s own _get_valid_actions method (which we can’t call) would give us the right coordinates — but we can approximate it by scanning the rendered frame for non-background, non-padding pixels and clicking those.
After clicking (selecting a piece), try ACTION1-4 moves and check if levels_completed increases or the grid changes toward win.

2. For bp35 (platformer):

ACTION3/4 are the only movement actions. ACTION6 clicks on visible interactive tiles.
The game exposes _get_valid_actions which returns actual clickable tile coordinates — this is available via available_actions in the frame... but the frame only gives raw ints [3,4,6,7].
Strategy: scan the bottom half of the visible frame for colored pixels (tiles), click them with ACTION6, and alternate with ACTION3/4 movement.

3. ACTION7 (undo) is critical for both games. If a move made the grid worse (no change in levels_completed, or same grid hash repeated), undo and try a different action. This is the core of the improvement over random.