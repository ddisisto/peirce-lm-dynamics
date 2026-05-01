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

---

## 2026-05-01 — representative-deep dip: six selected candidates all resolve to asymptotic basins by L_arch

**Commit:** `343e2fc` (broad-shallow baseline at `d18c693`).
**Run:** `uv run python scripts/representative_deep.py`
**Config:** model `EleutherAI/pythia-1b-deduped` (fp32, GTX 1070), initial `[BOS]`, six selected ranks from top-100 (0, 4, 6, 14, 27, 28), depth = `L_arch = 2048`, predicates EOS and window-cap, T=0 hard-cap.

### Headline

All six trajectories terminate as `window_cap` at length 2047 (zero EOS in any candidate). Each shows the basin-adjudication signature in late-window stats: chosen log-prob → 0, entropy → 0, alt-prob → 0. Each adjudicates as a true asymptotic basin under hard-cap T=0 by every signal in design-reqs v2.2.

### Per-candidate (early-64 vs late-64 averages)

| rank | branch    | L=64 cyc | L=2047 cyc | log_prob       | entropy      | alt_prob       |
|------|-----------|----------|------------|----------------|--------------|----------------|
| 0    | `\n`      | none     | 11         | -1.31 → -0.00  | 3.59 → 0.01  | 0.10 → 0.00    |
| 4    | 10 spaces | 4        | 4          | -0.46 → -0.00  | 1.38 → 0.02  | 0.03 → 0.00    |
| 6    | 11 spaces | 1        | 1          | -0.41 → -0.01  | 1.29 → 0.05  | 0.04 → 0.00    |
| 14   | 7 spaces  | 2        | 2          | -0.33 → -0.00  | 1.14 → 0.01  | 0.03 → 0.00    |
| 27   | 24 spaces | 1        | 1          | -0.24 → -0.02  | 0.83 → 0.14  | 0.03 → 0.01    |
| 28   | `_`       | 9        | 9          | -0.70 → -0.00  | 2.03 → 0.00  | 0.05 → 0.00    |

### Basin contents at L_arch tail (last 128 tokens, paraphrased)

- **Rank 0** (`\n`): period-11 phrase cycle, *"He is also the author of the Chromium browser."*
- **Rank 4** (10 spaces): period-4 markdown table fence, *"| `--` "*
- **Rank 6** (11 spaces): period-1 single-space repetition.
- **Rank 14** (7 spaces): period-2 pipe-bar fence, *"| | "*
- **Rank 27** (24 spaces): period-1 single-space repetition.
- **Rank 28** (`_`): period-9 phrase cycle, *"_first_ thing to note is that the "*

### Notable

- **Rank 0 is the strongest case for depth-as-adjudicator.** At L=64 the trajectory had escaped the local `\n → \n` kernel into freely-generated content (a contributor-list opening). At L=2047 it has settled into a period-11 *phrase* basin on entirely different content ("Chromium browser" authorship). The L=64 view could not have surfaced this; depth produced both the transient and the eventual basin. The intermediate journey lives in the per-step records.
- **Cycle period at L=64 matches cycle period at L=2047 for every candidate that flagged at L=64.** Token-level cycle detection at modest depth is a robust signal of eventual basin period *when it fires*. Absence at L=64 (as in rank 0) does not mean absence of basin — only that the basin lies past depth 64.
- **Rank 27 has the highest residual late-window pressure** (entropy 0.14, alt_prob 0.005). The 24-space basin is the loosest of the six. The other five are essentially deterministic in their late windows.

### Selection bias

Five of six candidates were selected because they flagged a token-level cycle in broad-shallow; rank 0 was selected as the model's argmax start. The set is biased toward trajectories likely to settle into basins. Whether non-cycling broad-shallow trajectories (the 68/100 unflagged) also reach basins by L_arch is a separate question this dip does not adjudicate.

### Suggestive but not yet adjudicated

- Whether non-cycling broad-shallow trajectories settle into basins by L_arch under hard-cap T=0.
- Whether multiple distinct broad-shallow trajectories converge to the same basin (basin coalescence vs basin multiplicity).
- Whether rank-27's higher residual pressure indicates a structurally looser basin or a token-position artifact at large initial-token width.

---

## 2026-05-01 — broad-shallow re-run with formalized basin probe + logit-gap field; basin coalescence confirmed at small budget

**Commit:** `ae95f32`
**Run:** `uv run python scripts/broad_shallow.py`
**Config:** model `EleutherAI/pythia-1b-deduped` (fp32, GTX 1070), initial `[BOS]`, top-100 from BOS, budget 64 tokens, T=0 hard-cap. Basin probe `peirce.basins.detect_tail_cycle` with `max_period=16`, `cycle_window=64`, `stats_window=32`. Six-field thin records (logit_gap added per design-reqs-records.md).

### Headline

- 32 / 100 trajectories formally flagged with tail cycles by the v1 probe — exactly the same count as the 2026-04-30 manual scan, which used the same algorithm at the same depth. Probe formalization reproduces the manual heuristic where designed to.
- 24 distinct basins identified across the 32 flagged trajectories. Basin coalescence is real: 3 basins absorb multiple trajectories.
- Cycle period range: 1 to 15. Late-window logit-gap range: 1.37 to 8.69. Late-window entropy range: 0.15 to 2.63.
- All 100 trajectories terminated as `budget_cap` (no EOS within 64 tokens), unchanged from prior run.

### Basin coalescence

The basin catalog is in [basins.md](basins.md); coalescence highlights:

- **basin-001** (period-1 single-space): 5 trajectories from whitespace-prefix and one mixed-prefix BOS branches (6, 27, 41, 64, 95).
- **basin-002** (period-2 double-space-pipe table fence): 4 trajectories (14, 19, 25, 62).
- **basin-003** (period-1 hash-fill `#`): 2 trajectories (49, 92).

The remaining 21 basins are singletons within this 100-trajectory ensemble. Coalescence is concentrated in the simplest structural basins; phrase-level and longer-period basins each appeared in only one trajectory at this scale.

### Phrase basins reached at budget=64

Four trajectories reached phrase-level cycles within budget — qualitatively different from structural / table-fence basins:

- Trajectory 28: `' the _first_ thing to note is that'` (period 9). Confirmed from prior runs.
- Trajectory 81: `' following is a list of all the files in the project.\n\nThe'` (period 15). Confirmed.
- Trajectory 93: `'\nThe data is released to the public.\n'` (period 10). New observation at this depth — the broad-shallow run reached a complete-sentence-period cycle in 64 tokens.
- Trajectory 3: `' I had been up for almost two hours and I was still awake.'` (period 14). Most natural-prose basin in the ensemble; loosest stats (H=2.63, gap=1.37) — possibly an extended transient that has not yet committed.

### What the new logit-gap field reveals

The mean late-window logit-gap separates basin family in a way that suggests it is a useful classification signal:

- Tightest basins (gap > 6): structural cycles dominated by very-low-period repetition or single-character fills (basin-010, -007, -021, -011, -006, -003, etc.).
- Loose basins (gap < 3): the prose-cycle basin-024 (gap=1.37), the multilingual basin-012 (gap=3.83), and the URL-pattern basin-016 (gap=3.09). These are candidates for extended-transient adjudication via depth extension.

The single-space basin-001 has gap=2.54 despite being period-1 — looser than the hash-fill basin-003 (gap=5.60) at the same period. The constituent trajectories enter the basin from different prefix lengths, with content-history affecting late-window certainty. Worth noting.

### Adjudicated

- **Basin coalescence is real, observable at small budget, and concentrated in the simplest basins.** Question raised in the 2026-05-01 representative-deep entry: settled in the affirmative for the structural family.
- **Phrase basins reach within 64 tokens for some trajectories.** The "_first_ thing to note" specimen (trajectory 28) was already known; "data is released to the public" (trajectory 93) is a new specimen of phrase-level basin reached at budget. The transients-as-territory thread now has clean specimens at small budget.
- **The v1 basin probe matches the manual heuristic where overlapping** — the 32/100 count is identical. The probe additionally produces structured signatures (period, cycle text, late-window stats) usable for the catalog.

### Suggestive but not yet adjudicated

- Whether the 68 / 100 still-transient trajectories reach basins by L_arch (the selection-bias question, unchanged).
- Whether the loose-stats basins (basin-024 prose-cycle, basin-012 multilingual, basin-016 URL-pattern) survive depth extension or escape into different content.
- Whether the gap-vs-H bivariate distribution across basins separates the local-success-trap family from other basin families more cleanly than either metric alone.
- Whether basin-001 vs basin-003 stats difference (period-1 single-space loose vs period-1 hash-fill tight) is a content-driven structural property or an artifact of constituent-trajectory diversity.

### Methodological observation

This is the first run that exercises the records-design probe shape `(window, records) → result` in code. The basin probe operates over a window-spec (`cycle_window`, `stats_window`) and produces a structured `BasinSignature` dataclass. The shape works in practice; the windowing parameters need empirical tuning as more specimens land. Probe-shaped detection also unblocks runtime basin-capture predicates (next move would be a predicate that runs the probe at intervals during generation and stops early on confirmed basins, freeing budget for non-cycling trajectories).

---

## 2026-05-01 — runtime basin-capture predicate; reps-count fix; v0.2 catalog

**Commit:** `08b0ba5`
**Run:** `uv run python scripts/broad_shallow.py`
**Config:** model `EleutherAI/pythia-1b-deduped` (fp32, GTX 1070), initial `[BOS]`, top-100 from BOS, budget 64 tokens, T=0 hard-cap. Predicate stack `[eos, basin_capture(K=4), budget_cap, window_cap]`. Probe `peirce.basins.detect_tail_cycle` at `max_period=16`, `cycle_window=64`, `stats_window=32`.

### Headline

- 28 / 100 trajectories captured by the runtime predicate (terminal `candidate-basin`); 72 / 100 reached `budget_cap`.
- 19 distinct basins identified across the 28 captured trajectories; 4 basins exhibit coalescence.
- Captured-trajectory length: mean 20, median 13, range 4–61. The runtime predicate frees ~44 inference forward passes per captured trajectory on average vs running each to budget cap.
- Catalog refreshed in [basins.md](basins.md) as v0.2.

### What changed since the v0.1 catalog (commit `ae95f32`)

Two coupled changes; the headline number drift (32 → 28 captured) is the joint effect.

1. **Runtime basin-capture predicate added.** Detection now fires during generation as soon as a confirmed cycle is observed, rather than running every trajectory to budget and probing the tail post-hoc. Probes every step once `n_steps >= K`; per-step overhead is bounded by `detect_tail_cycle`'s O(`max_period^2`) tail comparisons — negligible against a model forward.
2. **Confirmation threshold raised from K=2 to K=4** and **`repetitions_in_cycle_window` corrected.** v0.1 reported `tail_n // period` as the rep count, which is the trivial maximum given tail length and period rather than actual consecutive cycle blocks. Under that bug, K=2 sometimes flagged trajectories whose tail merely happened to contain a 2-token recurrence with prose elsewhere (period-1 cycles especially). With reps now counting consecutive cycle blocks back from the tail, K=4 is the empirical match to the v0.1-intent threshold "this cycle has structurally locked in" and matches the late-window pattern of every v0.1 catalog entry that ran to depth 64.

### Reconciliation against v0.1

- **All four high-coalescence v0.1 basins reproduced** with the same trajectory membership: single-space (5 traj), `'  |'` (4 traj), `'#'` (2 traj), and `' [x]'` (2 traj — v0.2 merges what v0.1 split into two rotational variants).
- **All three v0.1 phrase basins reproduced**: "first thing to note" (traj 28), "list of all the files" (traj 81), "data is released" (traj 93).
- **Five v0.1 entries not re-confirmed at v0.2 K=4**: `-trump` (period-3, traj 15), Japanese phrase (period-13, traj 37), `\n` (period-1, traj 40), status-table-row (period-14, traj 45), and the `I had been up` prose-cycle (period-14, traj 3). All were borderline at v0.1's K=2 and several were flagged "possibly extended transient" in the v0.1 catalog. None of these trajectories show 4 consecutive cycle reps within 64 tokens.

### Adjudicated

- **The runtime predicate matches the post-hoc probe in spirit and surfaces the same basin structure.** Coalescence pattern is identical at the high-coalescence end. No basin found by the runtime predicate is absent from the v0.1 universe.
- **The K=4 + corrected-reps threshold is more conservative than v0.1's K=2 + over-counted reps**, demoting borderline entries that were already noted as fragile in v0.1.
- **Inference savings are real and substantial** at this scale: ~44 forward passes saved per captured trajectory. Over 28 trajectories, ~1230 forward passes saved (vs ~6400 total in the v0.1 run).

### Suggestive but not yet adjudicated

- Whether the 72 / 100 unflagged trajectories reach basins by L_arch (the selection-bias question, unchanged — and now the natural next move under the runtime predicate, which will terminate them early on capture without depth budget waste).
- Whether the five demoted v0.1 entries materialize as confirmed basins when their trajectories are extended to L_arch under the v0.2 predicate. Specifically targeted candidates for the selection-bias probe.
- Whether basin-merging across rotational variants (basin-003 in v0.2 absorbed v0.1's basin-007 and basin-011) is a general pattern under the runtime predicate, or specific to short-period cycles where the K=4 termination point happens to align rotational starts.

### Methodological observation

The predicate signature was extended from `(history, n_steps) → tag | None` to `(history, records, n_steps) → tag | None` to support probes that need the per-step probability dynamics. Existing predicates (eos, budget_cap, window_cap) ignore the new `records` argument. Ordering in the predicate stack matters: `basin_capture` is placed after `eos` (so EOS termination still wins when the model produces `<|endoftext|>` mid-cycle) and before `budget_cap` (so capture-before-budget fires correctly).

The fix to `repetitions_in_cycle_window` retroactively affects how v0.1 catalog entries should be read: the rep counts in basins.md v0.1 were inflated. Basin identities (cycle-token-id tuples) and late-window stats are unaffected.
