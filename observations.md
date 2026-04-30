# Peirce — Observations

*Timestamped, append-only log of empirical observations from project runs. Each entry pins itself to a commit hash and repro details so that the observation remains interpretable even if the producing script later changes or is removed. The script does not need to keep working at HEAD; the entry's claim is "at commit X, running Y produced Z."*

*Deliberately not curated or pruned. Distilled findings, when warranted, belong elsewhere.*

---

## 2026-04-30 — first broad-shallow ensemble; document-start regime far from natural completion

**Commit:** `3d9d401`
**Run:** `uv run python scripts/broad_shallow.py`
**Config:** model `EleutherAI/pythia-1b-deduped` (fp32, GTX 1070), initial `[BOS]` only, breadth top-100 from BOS, budget 64 tokens, T=0 hard-cap inference.

### Aggregate

- All 100 trajectories terminated as `budget_cap`. **Zero EOS within 64 tokens** across the top-100 starts. The document-start regime under hard-cap T=0 is genuinely far from natural completion at this depth.
- Top-100 starting tokens cover 75.29% of BOS-distribution mass.
- 32/100 flagged a token-level tail-cycle under the simple detector (smallest period `p ∈ [1, 16]` for which the last `p` tokens repeat the `p` before).

### Patterns by surface kind of starting token

- **Whitespace / multi-space / `\t` → tabular cycles.** Trajectories 4, 6, 14, 19, 25, 27, 41, 45, 48, 57, 62, 63, 64, 78 settle into markdown-table fences (`| | | |`) or pipe-bar structures, mostly period 1 or 2. These are the cleanest token-level candidate basins.
- **Punctuation → memorized boilerplate openings.** `.`, `s`, `."`, `").`, `[@` all converge to *"The authors declare no conflict of interest. ![The flowchart of the study]..."* (medical-paper template). `;`, `a`, `\r` open into C/C++ header dumps (`#include <stdio.h>...`). `":` opens JSON-like structured text. None of these fire the token-level cycle predicate, but they are clearly semantic attractors at the content level.
- **Single letters and word-pieces → freer text** with no obvious basin within 64 tokens.

### Specific candidates for representative-deep adjudication

- Trajectory 6 (`'           '`, 11 spaces) and trajectory 27 (24 spaces): near-pure space repetition. Strongest period-1 fixed-point candidates.
- Trajectories 4, 14, 19, 25, 62: table-fence period-2 cycles (markdown table-row fences).
- Trajectory 28 (`_` branch, period-9 token cycle): *"The first thing to note is that the _first_ thing to note is that the _first_..."* — phrase-level cycle closed at the token level within budget.
- Trajectory 81 (`S` branch, period-15): *"The following is a list of all the files in the project. The following is a lis..."* — boilerplate-sentence cycle closed at token level.

### Cross-trajectory semantic patterns (not caught by token-level cycle detection)

- *"The first thing to note is that..."* appears in trajectories 28, 42, 52, 67, 80, 88, 98 — six independent starts converge to the same sentence opener.
- *"The authors declare no conflict of interest..."* converges from at least four different punctuation starts.
- Code-context tokens (`\n\n`, `[`, `\\`, `\xa0`, `\n\n\n`, `に`) drift into Chinese / Japanese-then-Chinese, frequently as code comments. The training distribution's multilingual code-context structure is visible at minimal context.

### Methodological observation

The per-step thin record view (`scripts/smoke_engine.py`) and the continuous-text-rendering view (`scripts/broad_shallow.py`) are different presentations of the same underlying trajectory records. The first reveals entropy and alt-token dynamics step by step; the second reveals semantic structure that token-level views obscure. Both should be available as views over the same underlying records once persistence lands.

### Suggestive but not adjudicated

- Whether trajectory 6 / 27 stay in the space-repetition basin asymptotically, or escape with greater context.
- Whether the boilerplate-opening semantic attractors are true asymptotic basins or extended transients (and what detector recognizes them — token-level cycle detection misses them entirely).
- Whether the multilingual drift (code-comment Chinese, Japanese→Chinese) reverses with depth or whether the trajectory commits to the second language.

These are representative-deep targets.
