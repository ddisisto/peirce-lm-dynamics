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

---

## 2026-05-02 — selection-bias probe to L_arch; capture is bimodal in depth; transient territory is substantive

**Commit:** `882ae6d`
**Run:** `uv run python scripts/selection_bias.py` (kicked off in background; output preserved at `/tmp/peirce_selbias.out`)
**Config:** model `EleutherAI/pythia-1b-deduped` (fp32, GTX 1070), initial `[BOS]`, top-100 from BOS, no budget cap, run to L_arch=2048 under hard-cap T=0. Predicate stack `[eos, basin_capture(K=4, max_period=32, cycle_window=256, stats_window=256), window_cap]`. Probe parameters extended from v0.2's `16/64/32` to admit longer-period phrase basins seen in the `343e2fc` representative-deep dip.

### Headline

- **61 / 100 trajectories captured** by the runtime predicate at L_arch (vs 28 / 100 at v0.2's broad-shallow budget=64). **39 / 100 reached `window_cap`** at length 2047 and remain uncaptured.
- **52 distinct basins** in the catalog after this run (up from 19 in v0.2). All 19 v0.2 basins reproduced with identical membership and signatures; 33 new basins surfaced at depth, predominantly long-period (11–26) phrase / boilerplate / table-row cycles. Catalog refreshed in [basins.md](basins.md) as v0.3.
- Capture-depth distribution: min=4, median=77, mean=107.4, max=844. Buckets: ≤64: 28, 65–256: 28, 257–1024: 5, 1025–2047: 0. Zero EOS in any trajectory.

### The bimodal-capture finding

Capture is effectively bimodal in depth. Trajectories that capture do so either by depth ≤ 64 (the broad-shallow regime) or in the next octave 65–256 (the modest-extension regime). Past depth ~1000 capture does not occur within L_arch in any of the 100 trajectories sampled. The 257–1024 bucket holds 5 trajectories (max=844, basin-024 `.data.cuda`); the 1025–2047 bucket is empty.

Read as a phase diagram: under hard-cap T=0 from `[BOS]`, a trajectory either *commits* to a token-level cycle within the first ~256 tokens of generation, or it doesn't commit within L_arch at all. There is no slowly-converging tail of late-cycle adoption — the bias of inference is to settle quickly or not settle.

This was not visible from the broad-shallow + representative-deep dip. The representative-deep candidates were all selected from the broad-shallow flagged set, biasing toward fast-capture trajectories. The selection-bias probe is the first run with non-biased depth-extension across the ensemble, and the bimodal cutoff is the first run-output it reveals.

### v0.1-demoted entries: four of five vindicated, one reassigned

Five v0.1 entries were demoted under v0.2's K=4 + corrected reps (trajectories 3, 15, 37, 40, 45). Selection-bias adjudicates them at L_arch:

- **Trajectory 3** (`I had been up for almost two hours and I was still awake.`): captured at length 91, period 14, H=2.66, gap=2.02. Now basin-022.
- **Trajectory 15** (`trump-`): captured at length 65, period 3, H=1.64, gap=5.99. Now basin-025.
- **Trajectory 37** (Japanese self-support phrase): captured at length 80, period 13, H=2.06, gap=3.35. Now basin-029.
- **Trajectory 45** (status-table-row): captured at length 87, period 14, H=1.32, gap=4.58. Now basin-033.
- **Trajectory 40** (v0.1 `\n` period-1 misassignment): captured at length 134, period 18, into the bilingual `file_content = 'Hello World!'` phrase basin (basin-031). The v0.1 period-1 `\n` cycle-token-id does not surface in this trajectory under K=4 + corrected reps; the eventual basin is the phrase, not the newline. The v0.1 assignment now reads as a misidentification — exactly the failure mode the K=2 + over-counted-reps regime was vulnerable to.

The four vindicated entries were real basins all along; v0.2's K=4 was conservatively stricter than v0.1's K=2 within the broad-shallow budget, but the basins materialize cleanly when extended to depth.

### What the new long-period basins look like

The 33 new basins are dominated by period-11-or-greater phrase cycles. Three patterns recur:

- **Recursive self-reference / self-quotation.** basin-030 (`The google-api-client library is a dependency of the google-api-client library`), basin-034 (`example of a simple example of a simple example of a simple example`), basin-035 (`is not a valid C++ program. It is not a valid C++ program because it`), basin-022 (`I had been up …`-style closure that re-invites itself). These are clean local-success-trap shapes — opening invites continuation that contains the opening, escape pressure never builds.
- **Template openers with multiple closures.** The `"The following is a list of all the …"` / `"The following is the list of all the …"` opener appears in three independent basins (basin-018 `files in the project`, basin-037 `people who have been involved in the creation of the new website`, basin-050 `available options for the download`). Three different completions of the same template, from three different BOS branches. The opener is an attractor; the noun phrase is the basin-distinguishing detail.
- **Memorized specific content.** basin-020 (`Chromium browser` authorship), basin-040 (a specific PubMed ID 17371263), basin-041 (RDoC project mental-disorder classification). The model has memorized very specific content and uses it as a basin target. Late-window stats are tight (gap 4.5–6.3) — once committed, these are essentially deterministic.

### What the 39 transient trajectories look like

Sampled tails (`window_cap` at 2047, last 64 tokens):

- **RFC enumeration**: `[RFC5294](...) - The Internet Assigned Numbers Authority (IANA)\n-   * [RFC5295](...) - ...` (traj 23, `'-'` start). RFC numbers increment monotonically; the structural pattern is constant but tokens never close a cycle.
- **Footnote enumeration**: `(636) (637) (638) (639) (640) ...` (traj 71, `'),'` start). Number incrementing.
- **Chronic-disease table-row**: `Chronic kidney disease ... Chronic obstructive pulmonary disease ... ` (traj 11, `'.'` start). Table rows enumerate distinct conditions.
- **CJK / Greek translation patches**: `"The Empire is in danger." "Η ΕΕ είναι σε θέση." ... "The Empire is in danger." "Η ΕΕ είναι σε θέση." ... ` (traj 8, `'"'` start; traj 31, `' "'` start). Translation pairs repeat but with msgid metadata that drifts.
- **Repeating user_user_user keys with version drift**: `user_user_user_id, user_user_user_name, user_user_user_email, user_user_user_created_at, user_user_user_updated_at, ...` (traj 53, `"';"` start).
- **Date-of-month enumeration**: `the eightieth day of the month, the nineth day of the month, the tenth day of the month, ...` (traj 82, `' since'` start).
- **Github issue enumeration / shield URLs**: `https://img.shields.io/github/issues/joshuamc/bootstrap-table/issues ... ` repeating with slight URL drift (traj 17, 12-space prefix).

Common shape: low local entropy (one obvious continuation at each step), no strict token-level repetition, structurally bounded by enumeration / drift. These are the candidates a token-level cycle detector cannot catch by construction.

### Adjudicated

- **Selection bias was real and substantial.** Broad-shallow capture is 28 / 100; depth-extended capture is 61 / 100. The 33-basin gap is the selection bias of the broad-shallow regime against long-period phrase basins. Reporting only broad-shallow capture would have understated basin density by more than half.
- **Capture-depth is bimodal under hard-cap T=0 from `[BOS]`**, with a sharp ~1000-token cutoff. Trajectories commit fast or not at all within L_arch.
- **"Transient territory" is substantive, not residual.** 39 / 100 trajectories — the largest single bucket — never close a token-level cycle within 2048 tokens. They are not bound for delayed cycles past depth 1000; they are in a different regime that the cycle-based detector cannot resolve.
- **All v0.2 catalog entries are reproducible at L_arch** with the same predicate, same membership, same cycle-token-ids. Catalog identities are stable across the broad-shallow → selection-bias depth axis.

### Suggestive but not yet adjudicated

- Whether the 39 transient trajectories would capture under a longer L_arch (sliding-window inference, future cycle), or whether they are structurally transient under hard-cap T=0 from `[BOS]`. The bimodal cutoff is suggestive of structural transience but does not strictly rule out very-late capture.
- Whether the bimodal-capture cutoff at ~1000 is a property of pythia-1b-deduped specifically, of the architectural L_arch=2048, or of hard-cap T=0 inference more generally. Cross-model and sliding-window comparisons would adjudicate.
- Whether the template-opener attractors (`"The following is a list of all the …"`) coalesce into a single super-basin under perturbation (the closures are interchangeable in some functional sense), or whether each closure is a structurally distinct basin. The cycle-token-id identity treats them as distinct; the catalog format may need a "basin family" relation when this question matures.
- Whether the recursive-self-reference shape (basin-030, -034, -035) is the dominant structural class of phrase basin in the model, or just a salient sub-class. A vocabulary-exhaustive ensemble would calibrate.

### Methodological observation

Probe parameters were extended (`max_period 16 → 32, cycle_window 64 → 256, stats_window 32 → 256`) before running. This was forced by the 343e2fc representative-deep dip, which surfaced phrase cycles at periods well above the v0.2 max_period=16. The catalog format (cycle-token-id identity) survives the parameter change cleanly: a basin found at one parameter setting is the same basin at another, as long as the cycle is reproducible. Probe parameters are part of run-pinning, not of basin identity.

The runtime predicate is now the bottleneck for cycle-based capture — it captures everything cycle-detectable and frees all the budget that would otherwise be wasted running cycle-captured trajectories to L_arch. The 39 uncaptured trajectories cost L_arch=2047 forward passes each; the 61 captured trajectories cost their median 77. Total forward passes ~ 39·2047 + 61·107 ≈ 86 k vs 100·2047 ≈ 205 k for an unconditional L_arch run — ~58% saved. The remaining inefficiency is structural: catching the long transients requires the next detector class.

The selection-bias probe is the closing observation of basin detection v1. The next direction is basin detection v2 (entropy-floor / logit-gap-floor) targeted at the 39 uncaptured trajectories, calibrated against the v0.3 catalog as confirmed-positive distribution.

## 2026-05-05 — persistence layer merged; dtype lands at fp16; aggregate deltas within boundary-case envelope

**Commit:** `6245a01` (merge of PR #1 from `persistence`)
**Run:** `uv run python scripts/broad_shallow.py && uv run python scripts/selection_bias.py` (artifacts persisted to `data/peirce.db`)
**Config:** model `EleutherAI/pythia-1b-deduped` (**fp16**, GTX 1070), initial `[BOS]`, top-100 from BOS, T=0 hard-cap. Broad-shallow: budget 64, K=4 with `max_period=16, cycle_window=64, stats_window=32`. Selection-bias: run to L_arch=2048, K=4 with `max_period=32, cycle_window=256, stats_window=256`. Selection-bias re-uses broad-shallow's 100 trajectories via the runner — trajectory rows cache-hit and the engine prefills from the existing 64 steps.

### Aggregate

|                | broad-shallow (budget 64) | selection-bias (L_arch 2048) |
|----------------|---------------------------|------------------------------|
| captured       | 29                        | 63                           |
| budget_cap     | 71                        | —                            |
| window_cap     | —                         | 37                           |

Distinct basins across the selection-bias ensemble: ~54 (estimate from PR body; not re-derived by re-running cycle detection on the persisted tails). Catalog v0.3 remains the canonical fp32 record.

### Headlines

- **Persistence layer landed.** Trajectory / observation split keyed by content-addressed hashes (blake2b-16 of canonical-JSON manifests). `data/peirce.db` holds 100 trajectories + 200 observations + 82,704 trajectory_steps in 12 MB. Selection-bias's 100 budget=64 prefixes hit the broad-shallow trajectory rows and extended via KV-cache prefill — the lensing-against-persisted-data capability the v2 design needs is now in hand.
- **Stack identity now includes dtype as fp16.** The persisted ensemble is a structurally distinct population from the fp32 catalog v0.3. Going forward, fp16 is the project default; v0.3 stays frozen as the fp32 record. This is a forward-consistency call, not a re-adjudication of v0.3.
- **Capture-count deltas are within the fp32 → fp16 boundary-case envelope.** Broad-shallow: 28 → 29 captured (+1). Selection-bias: 61 → 63 captured (+2). Distinct basins: 52 → ~54. Two-trajectory and two-basin shifts under T=0 hard-cap match the order-of-magnitude expectation for argmax flips at borderline log-prob ties under reduced precision. The deltas do not change the qualitative findings of the `882ae6d` selection-bias entry: bimodal capture distribution, ~1000-token cutoff, transient territory substantive (now 37/100 rather than 39/100), v0.2 basin coalescence membership unchanged.
- **Per-trajectory diffing deliberately deferred.** Identifying *which* trajectories flipped and *which* basins are new would require running cycle detection on the persisted tails and matching cycle-token-id tuples against the v0.3 catalog. Cost/benefit at this stage is poor: the roadmap doesn't move, the observations hardly change. The catalog as instrumented data source/sink is a future direction; until then, the present note is the record of the dtype transition.

### Methodological

- **The catalog as currently maintained is a hand-curated markdown artifact pinned to a specific run.** Re-deriving it across a stack-identity change is manual work disproportionate to the value at this stage. A future iteration will likely re-invent the catalog as a query over the persisted store rather than a hand-curated document, at which point dtype changes are no-cost.
- **The persistence layer's content-addressed identity scheme (stack + initial_ids + injections for trajectories; trajectory_id + predicates + inference_strategy for observations) makes the dtype boundary clean automatically.** No special handling needed — fp32 trajectory rows would coexist with fp16 ones in the same DB if both were generated, distinguishable by their stack hash. The store layer already carries the discipline that the catalog format does not yet have.

---

## 2026-05-06 — basin-v2 calibration probe; populations are inverted from the v1-detector intuition

**Commit:** `195e5c4` (basin-v2 branch; pre-design probe per ROADMAP).
**Run:** `uv run python scripts/v2_calibration_probe.py`
**Config:** read-only over `data/peirce.db` — the 100 fp16 selection-bias observations (predicate set `eos + basin_capture(K=4, max_period=32, cycle_window=256) + window_cap`, inference `hard_cap_t0`). For each trajectory, last-N feature panels over windows 32 / 64 / 128 / 256 / 512: mean and extreme (min for entropy / alt_prob, max for logit_gap / log_prob) per feature.

### Headline

The 37 `window_cap` trajectories — the v2 candidate-positive population — are *more* deterministic per-step than the 63 v1-captured trajectories, not less. Population separation is essentially complete on every (feature, window) cell; window size barely matters, which means the determinism is sustained, not a fragile artifact of any particular tail length.

### Population summary at window=256 (min / median / max)

| feature   | aggregator | candidate-basin (n=63) | window_cap (n=37)        |
|-----------|------------|------------------------|--------------------------|
| entropy   | mean       | 0.229 / 1.46 / 4.87    | 0.006 / 0.019 / 0.085    |
| logit_gap | mean       | 0.87 / 3.18 / 6.80     | 7.68 / 9.92 / 16.28      |
| alt_prob  | mean       | 0.020 / 0.065 / 0.165  | 0.000 / 0.001 / 0.011    |
| log_prob  | mean       | -2.68 / -0.88 / -0.06  | -0.021 / -0.003 / -0.001 |

Min over each window saturates at zero in both populations (entropy / alt_prob both bottom out trivially), so mean is the load-bearing aggregator for v2 thresholding. Logit_gap mean has the cleanest cushion — ~0.9-unit gap between the candidate-basin max (6.80) and the window_cap min (7.68) at window=256, with both populations preserving the cushion across all five window sizes tested.

### Mechanism, as `2026-05-01 EOS as implicit-success signal` foretold

The 37 transients aren't basin-adjacent under-pressure cases. They are clean local-success traps: at each step there's essentially one obvious continuation (entropy ~ 0, gap > 7), but the obvious continuations chain into ascending sequences and structural drift rather than fixed-token cycles. Eyeballing tails surfaces recurring shapes:

- **Numerical / temporal enumeration**: `**284. ** **285. **`, `(656) (657) (658)`, RFC5297→RFC5298, eightieth-day → nineth-day → tenth-day, `*AKT113* *AKT114*`.
- **Identifier-suffix concatenation** (most striking shape): `eval_with_mask_and_softmax_and_logits_and_softmax_and_logits.py`, `user_avatar_url_https_http_https_https'`, `var_name = var_name; return var_name;`.
- **Indexed figure / record drift**: `materials-12-01902-f064`, `ijerph-17-04281-g067` with running figure indices.
- **Boilerplate sentence with item drift**: chemical-detergent enumeration, brigade-assignment chain, alcohol-policy boilerplate.
- **Translation msgid/msgstr drift**: same Empire-in-danger string under incrementing bar01 → bar02 metadata.
- **Code structures with form drift**: helm yaml templates, Jupyter cell JSON, pub-fn-new self-call chain.

The v1 cycle-period detector is structurally blind to all of these by construction — the *content* never strictly repeats — but the entropy / gap floor is more extreme than for the cycle-captured population. v2-as-entropy-floor catches them.

### Implications for ROADMAP's open design questions

- **Detector signal: a single statistic suffices.** Entropy mean over a 256-window with threshold ~0.1 separates the populations cleanly. Logit_gap mean (threshold ~7) and log_prob mean (threshold ~-0.04) work equivalently. Multi-feature classifiers are not needed at this stage — the data is more separable than the design surface anticipated.
- **Basin identity for non-cyclical basins: flag-only-with-stats is the right first move.** The shapes inside the 37 are too varied to fingerprint with a tail-content tuple (the tails drift token-by-token), and template-pattern extraction is its own research problem. v2 captures the trajectory + late-window stats + a `basin_kind: noncyclical_local_success` flag. The cycle catalog stays cycle-only on basin identity; v2 adds an annotation channel rather than an alternative identity scheme.
- **Runtime cutoff vs post-hoc: runtime termination is safe from the first run.** ROADMAP's caution (probe-only first) was the right default before seeing the data. The actual data makes the false-positive rate at threshold ~0.1 essentially zero, given the v1-captured population's H_mean floor at 0.229.
- **Separator-vs-basin within enumerations**: the data doesn't directly resolve this, but it suggests the question may not matter for v2's predicate logic — both separators and incrementing tokens are highly determined; per-trajectory entropy averages over both. Inside-structure analysis is post-hoc, not predicate.

### Comparison-frame caveat

Captured trajectories were terminated by the v1 predicate (lengths 4–575) and so their "late-window" reflects *up to capture*, not stable-in-basin asymptote — the v1 predicate hides what comes after. The shortest captures (lengths 4–17, H_mean 4–4.5) are at the opposite extreme from the 37: very-early broad-shallow whitespace / table-fence captures where there's no room for the late window to settle. They're noisy in this comparison frame but irrelevant to the v2 threshold question because they're trivially-cyclical. Substantive captures (length ≥ ~50) span the entropy range 0.23–2.96, well separated from the 37 transients.

The natural next move is implied by the caveat — see [ideas.md](ideas.md) "v2-only re-extension of the broad-shallow ensemble" entry.

### Adjudicated

- **Single-statistic v2 is sufficient on this calibration.** Multi-feature framing is overkill for the separation observed.
- **Runtime-mode v2 is safe from the first run** under threshold ~0.1 entropy mean over a 256-window. Probe-only intermediate is unnecessary.
- **The 37 are not late-cycle-adoption candidates.** They are a structurally distinct regime from the v1-cyclic basins; v2 catches them via a *different signature* (per-step certainty without content-level period), not via a more sensitive version of the same signature.

### Suggestive but not yet adjudicated

- Whether v1-captured trajectories continue to satisfy the v2 entropy criterion past their capture point, or whether some cycle-captured basins are looser-entropy than the v2 threshold and would not be jointly captured. The candidate-basin H_mean range (0.23 to 4.87) suggests at least the high-entropy end (the prose cycles, "I had been up", "first thing to note") would *not* fire v2 at threshold 0.1. v2 and v1 may detect overlapping but distinct basin populations rather than v2 strictly subsuming v1.
- Whether the short broad-shallow captures (length ≤ 17, H_mean > 4) actually settle if extended past v1 capture into a v2-detectable regime, or whether they remain in their loose late-window stats. v1's K=4 confirmation may be firing prematurely on these.
- Both questions resolve under the v2-only re-extension run named in [ideas.md](ideas.md).

---

## 2026-05-07 — depth-collapse confirmed: entropy floor is universal, not basin-class-specific

**Commit:** `1e5710e` (basin-v2; full-depth extension landed at `fa10933`, probe updated at `1e5710e`).
**Run:** `uv run python scripts/full_depth_extension.py && uv run python scripts/v2_calibration_probe.py`
**Config:** `data/peirce.db` now holds 100 trajectories × 2047 materialized steps each. The extension run wrote 100 fresh `window_cap` observations under predicates `[eos, window_cap(L_arch=2048)]` only — no v1 cycle-capture. The calibration probe was updated (same commit) to read `obs.trajectory.steps` (the full materialized trajectory) rather than `obs.steps` (truncated to `observed_length`); the original selection-bias terminal_event labels are kept for population definition.

This entry corrects the framing in the prior 2026-05-06 entry. The headline of that entry — "the 37 are *more* deterministic per-step than v1-captured ones" — was a true statement about the truncated late-windows it measured but a misleading framing of the underlying phenomenon. With full-depth data the picture inverts.

### Headline

**Daniel's depth-collapse hypothesis is confirmed in the strong form.** Per-step entropy is a *depth* phenomenon, not a basin phenomenon. By position bucket `[1024, 2048)` the candidate-basin and window_cap populations are statistically indistinguishable on entropy mean, with all 100 trajectories below ~0.13 and 96/100 below 0.1.

### Population convergence by position bucket (entropy mean, median across trajectories)

| bucket           | candidate-basin (n=63) | window_cap (n=37) |
|------------------|------------------------|--------------------|
| `[0, 64)`        | 1.86                   | 2.08               |
| `[64, 256)`      | 0.19                   | 0.49               |
| `[256, 1024)`    | 0.027                  | 0.069              |
| `[1024, 2048)`   | **0.010**              | **0.022**          |

Maxima at the deepest bucket: candidate-basin 0.134, window_cap 0.096 — overlap. Logit_gap mean medians at `[1024, 2048)`: 9.35 vs 9.79, also overlapping. The clean separation reported in the prior calibration entry was an artifact of comparing v1-captured trajectories at *capture-point depth* (lengths 4–575, where they hadn't reached the floor yet) against window_cap trajectories at L_arch.

### Onset is uniform across populations

Per-trajectory position at which entropy first stays below 0.1 for 8 consecutive steps:

| population         | n  | min | p25 | p50 | p75 | max | never_below |
|--------------------|----|----:|----:|----:|----:|----:|------------:|
| candidate-basin    | 59 | 28  | 109 | 174 | 232 | 616 | 4           |
| window_cap         | 37 | 25  | 76  | 143 | 298 | 612 | 0           |

Distributions overlap. Window-cap trajectories settle slightly faster on the median (143 vs 174) but the IQRs and ranges are essentially the same. No trajectory ever crosses below threshold past 616 — the deterministic floor is reached well within `[256, 1024)` for all trajectories that reach it at all.

### The 4 "never-below" candidate-basins reveal a cycle-period signature

The four candidate-basin trajectories that never have 8 consecutive sub-0.1 steps are not the loose prose-cycle entries. They are trajectories whose cycle period structure shows up in the entropy time-series — *within-cycle* entropy oscillates because some cycle positions are deterministic and some are not, so the smoothing requirement is never satisfied:

- `ada5657f` — basin-006 (`%22%22+` URL fragment, period 5). Bucket-mean entropy at `[1024, 2048)` is 0.028, below threshold; but within-cycle one or two positions have local entropy spikes large enough to prevent an 8-step sub-0.1 run.
- `b9eeb9e9`, `e3da051e` — hash-fill cycles with `\n\n#` periodicity inside.
- `ba1fa91a` — length-4 capture, all-whitespace tail; the only one of the four whose bucket-mean (0.134) is also above threshold.

This is itself a useful signal: cycle period detected via the *entropy time-series* rather than the token sequence. Worth noting for the v2 design space — the cycle detector doesn't have to operate on token-id tuples to find period structure.

### Post-capture behavior is varied — the catalog mixes asymptotes with transients

Reading the full-depth tails for v1-captured trajectories surfaces three regimes:

- **Phrase cycles persist and consolidate.** `acb1a7ab` (basin-020 Chromium) had H_mean=2.055 at v1 capture (length 221) and H=0.005 at `[1024, 2048)`. `fe999045` (basin-022 "I had been up") goes from H=2.633 at length 91 to H=0.010 at depth. The cycle was real at capture; it tightened further with depth. These are asymptotic basins.
- **Some short-period captures morph into recursive concatenation.** `6917c95f` was cataloged as basin-023 (`_v6` period 3) at length 302. At full depth its tail reads `ip6_tables_v6_ext_v6_v6_v6_v6_v6_v6_v6_v6_v6.h>` — the `_v6` period broke and the trajectory escaped into recursive identifier concatenation. `58ca117f` (a `vlan6` family capture) shows the same pattern: `vlan6_vlan6_vlan6_vlan6_vlan.h>`. `62498529` shows `_name_name_name_name…` recursive expansion. The v1 cycle was a *transitional* moment, not the asymptote.
- **Very-short captures (length 4–17) mostly do settle**, but into varied shapes — some into the v1-captured cycle (table fences, code fences), some into different attractors. Worth case-by-case re-validation.

So the basin catalog as currently maintained mixes asymptotic basins with transitional moments. v1 is correctly a "cycle moment detector" but mis-named when the captured cycles aren't asymptotic. The catalog v0.3 entries that turn out to be transitional deserve a different annotation.

### Reframing v2

The entropy-floor / logit-gap-floor framing in ROADMAP and the prior calibration entry no longer tracks any meaningful basin distinction. The depth-collapse means:

- **Entropy as a v2 detector signal is the wrong axis.** Every trajectory at depth has near-zero entropy. A threshold-based predicate fires on essentially all of them at sufficient depth — it's a depth-detector, not a basin-detector.
- **The interesting v2 question is *content shape at depth*, not *whether* the model commits.** All trajectories commit. What they commit to varies — token-level cycle, ascending sequence, recursive concatenation, drift with template invariants — and these shapes are likely the cleaner cataloging axis than presence/absence of period.
- **v1 catches one content shape (token-level period); v2 should catch the others.** Re-cast: v2 detects ascending / drift / concat shapes that v1 is structurally blind to. The detector for those probably operates over *position-content invariants* (template structure, suffix-extension patterns) rather than over the entropy distribution.
- **Runtime predicate value drops sharply.** Inference savings from runtime termination are gone if v2 needs depth ≥ ~1024 to characterize the asymptote. v2 may live mostly as post-hoc analysis over fully-extended trajectories — exactly the substrate the full-depth extension produces.

### Adjudicated

- **Per-step entropy collapse is a depth phenomenon, not a basin phenomenon.** All 100 trajectories converge to a tight entropy floor by `[1024, 2048)` regardless of v1-detected basin status. The 37 "transients" aren't transient — they are at the same deterministic floor as everyone else.
- **The 2026-05-06 calibration entry's headline finding is a truncation artifact.** The single-statistic v2 detector it suggested would not work — entropy doesn't separate basin classes once both populations are observed at full depth.
- **Some v1-captured "basins" are transitional, not asymptotic.** The `_v6`, `vlan6_`, `_name` family in particular escape their captured cycles into recursive concatenation. The catalog needs re-validation against post-capture asymptotes; the cycle-token-id identity remains valid, but the basin-as-asymptote claim does not for these entries.
- **Cycle period detectable in entropy time-series.** The 4 never-below candidates reveal that entropy oscillation within a cycle is a separate, period-revealing signal independent of token-id matching.

### Suggestive but not yet adjudicated

- **What the right v2 detector shape is.** Content-shape classifier at depth (cycle / ascend / concat / drift) is the working candidate; whether a clean operational definition exists for each shape, and whether the shapes are mutually exclusive or overlapping, is a research question this finding makes urgent.
- **Whether the "transitional v1 capture" pattern is general** or specific to the short-period structural family. The phrase-cycle captures (Chromium, "first thing", etc.) all persisted and tightened. Among the short structural captures, some persisted (e.g. PubMed URL repeat) and some escaped (`_v6`, `vlan6_`). Whether the difference correlates with cycle period, content domain, or some other feature is open.
- **Whether content-shape regimes are predictable from early-window features.** If we can classify shape from `[64, 256)` features, we recover most of the runtime-predicate value. If we can't, v2 is necessarily post-hoc.

### Methodological

- **The persistence layer + content-addressed identity made this finding cheap to obtain.** Once full_depth_extension.py landed, all subsequent analysis is read-only over the store with no further inference. The probe edit (one line: `obs.steps` → `obs.trajectory.steps`) was the only code change needed to surface the corrected picture. The trajectory-vs-observation split in `peirce.records` is doing exactly what it was designed to do — multiple observation rows sharing trajectory_steps, the longer one extending the shorter without re-running.
- **The 2026-05-06 calibration entry's discipline of pinning to a commit means it remains true and reproducible against `195e5c4`'s data view.** The reproduction protocol surfaces exactly what the entry reported. The interpretation correction is what landed in this entry, not a rewrite of the prior entry. Append-only working as designed.
- **The full-depth extension is now the canonical lens for v2 calibration.** Future v2 work operates over `data/peirce.db` post-extension as a fixed substrate; iterating on detector shape doesn't require re-running inference.
