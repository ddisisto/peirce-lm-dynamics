# Peirce — Observations (Cycle 2)

*Append-only commit-pinned log of empirical findings. Each entry pins to a commit hash and includes the run command(s) needed to reproduce. Scripts can evolve or die; entries reproduce from the commit they pin.*

*Cycle 1 entries: see [`archive/observations-cycle-1.md`](archive/observations-cycle-1.md) (preserved in full; reproducible from commits at or before the `v0.1-final` tag).*

*Cited 8-char hex prefixes in entries below are `trajectory_id[:8]`, naming the persistent identity of each BOS-branch trajectory in `data/peirce.db` (`trajectory_id = hash(stack, initial_ids, injections)`). Entries committed before the 2026-05-11 renderer-refactor pass cited `observation_id[:8]` from the C1 selection-bias predicate set (`observation_id = hash(trajectory_id, predicates, inference_strategy)` under retired predicates `[eos, basin_capture(max_period=32, cycle_window=256), window_cap]`); those have been backfilled in place to trajectory_id prefixes for layer-consistency and forward stability under predicate-set changes.*

---

## 2026-05-09 — N1 first-light: slot/scaffolding decomposition over the 100-trajectory substrate

**Commit:** `8631813`
**Run:** `uv run python scripts/phase_aware_chosen.py`
**Config:** read-only over `data/peirce.db`. 100 fp16 selection-bias observations, deep window `[1024, end)`, period detection via autocorrelation peak in lag ∈ `[2, 128]` with `peak_min = 0.3`, slot threshold `chosen-token H > 1e-3` nats.

### Headline

The slot/scaffolding decomposition over the substrate produces a clean three-way partition: 19/100 trajectories have at least one slot, 78/100 have a detected period but no slots (every phase pinned to a single chosen token across recurrences), 3/100 have no detected period. Within the 19 slotted trajectories, a sub-partition not anticipated by the project's vocabulary surfaces immediately: **counter slots** (chosen tokens enumerate consecutive integers / alphabet letters across recurrences, mechanical successor) versus **class slots** (chosen tokens rotate over a small semantic class). One textbook class-slot specimen — `49ba0b75`, period 43, single slot at phase 0 emitting ` first`/` second` with empirical alt-distribution including ` contact` — proves the slot-readout operation works as the foundation predicts.

### Aggregate counts

- **SLOTTED** (≥1 phase with chosen-token Shannon entropy > 1e-3 nats across recurrences): 19/100
- **SCAFFOLD-only** (period detected, every phase chosen-pinned): 78/100
- **NOPERIOD** (no autocorrelation peak ≥ 0.3 in lag window): 3/100

### Proof-of-concept class slot

- **`49ba0b75`** — period=43, floor_H=0.0047, osc_amp=0.2211, slots=1/43.
  - phase=0, n_recur=24, chosen_H=0.679 nats (≈ ln(2)).
  - chosen distribution: ` first`×14 (0.58), ` second`×10 (0.42).
  - alt distribution: ` second`×12 (0.50), ` first`×9 (0.38), ` contact`×3 (0.12).

The chosen distribution is binary; the alt distribution is the chosen distribution swapped (each recurrence's runner-up is the other slot member) plus a third token, ` contact`, never picked but flagged as alt 3 times. Reading ` contact` as the model's pulled-aside third candidate gives a non-trivial datum about the model's local prior over this slot's class — exactly the readout the project's vocabulary names.

### Counter slots — an unexpected sub-class

Specimens whose slot chosen-tokens form a successor sequence (consecutive integers, alphabet letters), not a discrete class:

| oid | period | slots | slot phase | chosen sample | n_recur | chosen_H |
|---|---|---|---|---|---|---|
| `13f9cd8d` | 29 | 1/29 | 18 | `'36','37','38','39','40','41',…` | 35 | 3.555 |
| `d24c9484` | 22 | 1/22 | 4 | `' 40',' 41',' 42',' 43','44',…` | 47 | 3.850 |
| `d2562221` | 19 | 1/19 | 9 | `'r','s','t','u','v','w','x',…` | 54 | 3.251 |
| `1f812a06` | 7 | 1/7 | 2 | `'147','148','149','150','151',…` | 146 | 4.984 |

These are real slots under the chosen-H criterion but the "class" being read out is "successor of the previous recurrence's emission." Mechanism is plausibly induction-head copy + increment, distinct from the FV-head class-conditioned-generation hypothesis the project's class-enumeration framing implies. The vocabulary should distinguish: the slot-readout *operation* is the same (alt distribution at the slot phase), but the *interpretation* of the readout differs sharply between counter and class cases. A counter slot's alt distribution is dominated by neighbours-of-the-counter-value (` 45`×2, ` 50`×2, ` 53`×2 at d24c9484's slot) rather than alternative class members.

### Period-detection harmonics: `slots = N / N` specimens

Seven specimens come up as SLOTTED with every phase a slot and uniform chosen_H values (5f3c1e41, 9bde3a7a, a36f4b57, fffba0e8, 0a52701d, a2cfa7d4, 60e599bd). Inspection of the first specimen (`5f3c1e41`, period=96, slots=96/96, all phases chosen_H=1.768 nats ≈ ln(6)) shows the chosen distributions across phases are rotations of the same six-token set. This is a period-detection-aliasing signature: the true cycle period is an integer divisor of 96, and `dominant_period`'s argmax-in-`[2, 128]` logic picked the harmonic. The current `dominant_period` returns `argmax(autocorrelation[lag_min:lag_max+1])` — *highest* peak in the window, not *first* peak above threshold. Fix is to switch to first-peak-above-threshold; touches `scripts/plot_trajectories.py` (where the function originates) and N1 (which currently inherits the bug). Records the issue here rather than fixing in the same step because the substrate-shape-metric `period` is a contract-level quantity and the fix should propagate consistently.

### Single-mode template cycles (high-osc-amp SCAFFOLD specimens)

The SCAFFOLD bucket is internally heterogeneous. High-osc_amp specimens like `edb2b7cf` (period=116, osc_amp=0.3841), `8ea1fab2` (period=25, osc_amp=0.2530), `fa70f050` (period=26, osc_amp=0.1657) have detected periods, every phase pinned, and substantial within-cycle entropy oscillation. The trajectory repeats a fixed token-template; some positions in the template are naturally higher-H than others (the model has rotational potential there) but always commits to the same token. This is the textbook single-mode-template-cycle / R2 specimen. Compare to slotted specimens at similar osc_amp (`49ba0b75` osc_amp=0.2211, `13f9cd8d` osc_amp=0.3120): the *shape* of the entropy oscillation is similar, but only the slotted specimens actually rotate the chosen token at the high-H phases.

### NOPERIOD specimens — three trajectories

- `48a13037`: floor_H=0.0012, osc_amp=0.4071 (highest osc_amp in the entire substrate)
- `7c66ed46`: floor_H=0.0018, osc_amp=0.1055
- `4e26d572`: floor_H=0.0016, osc_amp=0.0809

These have measurable entropy oscillation but no autocorrelation peak ≥ 0.3 in the search window. Not single-mode cycles (osc_amp too high). Not phase-partitionable by N1 (no period). These need a different tool — drifting / quasi-periodic / multi-period analysis. The `48a13037` specimen having both the lowest floor_H and the highest osc_amp in the substrate is the kind of edge case worth singling out for direct trajectory inspection.

### Follow-ups

- **Period-detection refinement.** Switch `dominant_period` from argmax to first-peak-above-threshold; promote to `peirce/shape.py` once a third consumer warrants it. Re-run N1 + `plot_trajectories.py` + `high_h_readout.py` after the change to see the catalog under corrected periods.
- **Counter-vs-class sub-partition.** Either tag this in N1's output (heuristic: are the slot's top chosen tokens lexically/numerically consecutive?) or land it as project vocabulary. The mechanism distinction (induction-head succession vs FV-head class generation) is testable in Pythia by head-ablation, listed under N4 follow-ups in `lit-review.md`.
- **NOPERIOD specimen direct inspection.** Render the deep-window entropy trace and chosen-token sequence for `48a13037`; ask whether it's drifting (period changes over the window), quasi-periodic, or genuinely aperiodic.
- **Slot-readout under inference.** The empirical alt distributions reported here are top-1-alt-only (the persisted record carries one alt per step). Full-distribution slot-readout would require re-running inference at slot positions and capturing the rank-1..rank-K distribution; this is N3-adjacent (seeded class-enumeration uses the same machinery) but worth noting as a distinct future move if the empirical alt readouts continue to surface interesting class structure.


## 2026-05-10 — N1.5 catalog: shape catalog under v0.2 vocabulary

**Commit:** `3be3208`
**Run:** `uv run python scripts/shape_catalog.py`
**Config:** read-only over `data/peirce.db`; 100 fp16 selection-bias observations; deep window `[1024, end)`; period detection via `peirce.shape.acf_peaks` (local maxima ≥ 0.3 in lag ∈ [2, 128]); slot threshold chosen-token H > 1e-3 nats; counter heuristic int/letter consecutivity at match-fraction ≥ 0.75; gap_over_H per step computed as `gap / max(entropy, 1e-4)`.

### Shape primitive contract revision

The autocorrelation peak list is the underlying period-structure measurement; calling any single integer "the period" is a convention over that list, with characteristic failure modes for any single rule. `design-reqs.md` now lists `peaks` as a shape primitive and `period` as a single-int convention layer over it. Current convention is divisor-aware: smallest in-list divisor of the strongest peak; falls back to the strongest peak when no in-list divisor is found. Convention is revisable; convention disagreements are auditable by inspection of the `peaks` field on every catalog row.

The shape primitives `entropy_onset`, `acf_peaks`, `dominant_period` are promoted from the inlined copies in `scripts/plot_trajectories.py` and `scripts/phase_aware_chosen.py` to a shared `peirce/shape.py` module. Both existing consumers updated to import from there; the catalog is the third consumer that warranted the promotion.

### Partition counts under the corrected convention

- **SLOTTED:** 26 / 100
  - CLASS: 17
  - MIXED (multi-slot trajectory with both counter and class slots): 2
  - COUNTER-INT: 6
  - COUNTER-LETTER: 1
- **SCAFFOLD:** 66 / 100
- **NOPERIOD:** 8 / 100

Comparison to N1 first-light (under the prior argmax-in-window period rule, observation `b394044`): SLOTTED 19 / SCAFFOLD 78 / NOPERIOD 3. The three-way structure is robust to the convention change; specifics shifted as ~7 specimens moved SCAFFOLD → SLOTTED (harmonic-aliased trajectories now reading at the fundamental period and showing slots) and ~5 moved PERIODIC → NOPERIOD (specimens with monotonically rising acf into out-of-window, now correctly excluded by the strict-local-max definition rather than picking up `lag_max` as argmax).

### Diagnostic specimen verdicts under the new convention

- **`49ba0b75`** (textbook class slot): period=43 (prime), peaks=[(43,0.92), (86,0.90)], slot at phase 0, chosen=` first`×14 / ` second`×10, alt=` contact`×3. Recovers N1 first-light reading.
- **`13f9cd8d`** (counter slot): peaks include both fundamental at 29 (acf 0.96) and weak sub-periodicity at 7 (acf 0.40); divisor rule correctly returns 29 (29 % 7 ≠ 0). Slot at phase 18, chosen=`36`/`37`/.../`70`, delta evidence median=+1, frac=1.00 → COUNTER-INT. Recovers N1 first-light reading.
- **`fa70f050`** (nested 2-and-26): peaks=[(2,0.44),(24,0.44),(26,0.97),(28,0.42),(50,0.43),(52,0.93),...]; divisor rule returns 2 (smallest in-list divisor of strongest=26). Period-2 alternation captures the within-cycle structure cleanly; the 26-period harmonic structure is preserved in the peaks field.
- **`5f3c1e41`** (chosen-token / H-trace period divergence): peaks=[(96,0.62)] only. 96/96 slots at chosen_H=1.768 ≈ ln(6) — i.e. 6 distinct tokens rotating across phases. The chosen-token rotation has period 96/6=16, but the entropy timeseries autocorrelation at lag 16 sits below `peak_min=0.3`. The catalog reports the H-trace measurement honestly (no detectable lag-16 peak) and the divergence is visible in the slot-readout (rotation pattern across the 96 phases is the same 6-element class). A real subtlety: chosen-token-rotation period and acf-of-H-trace period can diverge; the catalog doesn't fabricate the rotation period from the chosen tokens.

### SCAFFOLD commitment-strength heterogeneity

Position-resolved gap readouts surface the within-SCAFFOLD heterogeneity. Examples:

- **`edb2b7cf`** (period=116, osc_amp=0.3841, peaks=[(116,0.87)] single peak): commit-soft phases at gap_med ≈ 0.27 (chosen=`------`, `~~~`) alongside commit-hard phases at gap_med ≈ 39.75. The trajectory carries a fixed token-template with extreme intra-template commitment variance.
- **`052ebc5a`** (period=22, full harmonic ladder peaks=[(22,0.98),(44,0.96),(66,0.94),(88,0.92),(110,0.90)]): one near-bifurcation phase at gap_med=0.469 (chosen=` "`) with the rest at 7+ — a single weakly-committed phase within an otherwise strongly-pinned scaffold.
- **`4a211c24`** (period=63 fundamental, peaks include weak side-peaks at lags 2, 61, 65, 126, 128): the side-peaks at 61/65 and 126/128 are 63±2 / 126±2 — period-2 sub-structure interfering with the period-63 fundamental, visible directly in the peak list.

### Counter-vs-class as a description tool

With N=6 COUNTER-INT / N=1 COUNTER-LETTER / N=17 CLASS / N=2 MIXED, the heuristic is descriptive at this sample, not a classifier. The catalog reports the underlying delta evidence (int and letter delta median + match-fraction) under each slot row, so the convention's tag is auditable per-slot. Counter slots in the substrate display essentially perfect arithmetic structure (median delta = +1, match-fraction = 1.00 in the typical case); class slots show no integer or letter consecutivity (delta evidence reads as N/A). The mid-cases the heuristic was designed to surface — partial-counter-with-noise, or class-rotation-that-happens-to-be-numerically-ordered — do not yet appear in the substrate.

### N2 candidate hand-off

The catalog's principled candidate list (lowest gap_over_H positions in the deep window) is dominated by `49ba0b75`'s slot positions (chosen=` first` / ` second`, gap_over_H ≈ 0.0–0.2) — the textbook class-slot's near-bifurcation moments, which is what the principle would predict. The simplest baseline list (highest H positions) tops out at the NOPERIOD specimen `48a13037` at H=4.68 and the COUNTER-LETTER specimen `d2562221`. Both lists ship in the catalog output for N2 to consume.

### Follow-ups

- **NOPERIOD specimen audit.** Now 8 specimens (was 3); the `48a13037` highest-osc_amp one is still the most interesting. The 5 new NOPERIOD additions are likely monotonically-rising-acf-into-out-of-window trajectories that the strict-local-max rule correctly excludes; worth confirming by inspecting their peak lists (which should be empty under the current threshold) and considering whether a wider lag window or lower peak threshold is warranted for any of them.
- **Counter-vs-class with N=6/17.** The heuristic is descriptive at this sample. Lifting into project vocabulary requires more specimens (or seeded probing under N3) to populate the mid-cases.
- **`5f3c1e41` chosen-token-period vs H-trace-period divergence.** The catalog reports both signals honestly but the catalog doesn't currently *name* the divergence. If more such specimens emerge, a named tag (e.g. `SLOTTED-ROTATION-AT-HARMONIC` or similar) may earn its keep.
- **Regime-vocabulary canonisation (`design-reqs.md` "Open: regime vocabulary").** Precondition 1 (mechanical re-derivation from shape signals) is now effectively met by the catalog. Precondition 2 (renaming consideration vs Markov-chain prior art — Geng 2603.11228, Zekri 2410.02724) is the remaining work.


## 2026-05-10 — NOPERIOD specimen audit: two-cluster substructure within the no-period bucket

**Commit:** `af8d141`
**Run:** `uv run python scripts/noperiod_audit.py`
**Config:** read-only over `data/peirce.db`; same selection-bias filter as `shape_catalog.py`. Per NOPERIOD specimen, peaks at default + relaxed `PEAK_MIN ∈ {0.20, 0.10}`, peaks under widened `LAG_MAX = 256`, top-K normalized-acf values across the wide window with no strict-local-max filter, plus deep-window H / gap / gap_over_H quartile summaries.

### Headline

The 8 NOPERIOD specimens partition cleanly into two empirical clusters. Five (the new NOPERIOD additions from the N1 → N1.5 convention shift) are honest no-period: low-amplitude smooth H-traces with a monotonically declining autocorrelation and no peak at any tested threshold or lag window. Three (the original N1 first-light NOPERIOD set) carry weak quasi-periodic structure visible at relaxed `PEAK_MIN`, sitting on a bimodal H-trace — near-zero floor punctuated by isolated high-uncertainty spikes. The strict-local-max + `PEAK_MIN = 0.30` convention does the right thing on both: Cluster A is genuinely structureless and Cluster B's structure is too weak / sparse to lift into the catalog's PERIODIC bucket without bringing in false positives. The catalog's NOPERIOD tag therefore correctly groups them, and the within-NOPERIOD substructure is descriptive — surfaced here for downstream consumers (especially N2) but not currently load-bearing.

### Cluster A — honest no-period (n=5)

`9af67bb8`, `53e800cb`, `5b628579`, `7c7228bf`, `c82e06a6`. Deep H median 0.05–0.13 nats, deep gap 5–7 logits, gap_over_H median 40–120. The deep H-trace is smooth and slow-varying around its low floor; the autocorrelation declines monotonically from acf ≈ 0.99 at lag 2 to lower values at higher lags, with no strict local maximum at any tested `PEAK_MIN ∈ {0.30, 0.20, 0.10}` over `lag ≤ 256`. The high acf at small lags reflects the smoothness, not periodicity.

These 5 are exactly the specimens the convention shift correctly reclassified PERIODIC → NOPERIOD: under the prior `argmax`-in-window rule they would have returned `lag_max = 128` (the highest-acf lag in a monotonically declining curve sits at the boundary), which the strict-local-max rule rejects because `ac[lag_max]` has no right neighbour to strictly exceed.

### Cluster B — weak quasi-periodic structure on bimodal H (n=3)

`48a13037`, `7c66ed46`, `4e26d572`. Deep H median ≈ 0.001–0.002 nats but max 1.3–5.2 nats — a sharply bimodal trace: long stretches of near-zero entropy punctuated by rare high-uncertainty events. Deep gap median 9–10 logits, gap_over_H median 5500–8200 with IQR widths spanning order-of-magnitude (e.g. `48a13037` IQR `[774, 57392]`, max `425625`). The bimodal H produces the bimodal gap_over_H — most positions are super-committed (huge gap_over_H), a few are wide-open (small gap_over_H, possibly < 1).

Sub-threshold periodic structure is visible at relaxed `PEAK_MIN`:

- `48a13037`: peaks at `PEAK_MIN=0.10` are `[(109, 0.13)]` over `lag ≤ 128`, extending to `[(109, 0.13), (210, 0.13)]` over `lag ≤ 256`. The lag-210 peak is approximately `2 × 109` — a weak harmonic ladder consistent with a fundamental near 109. Top raw acf in the wide window: 0.13 at lag 210 / 0.13 at lag 109 / 0.10 at lag 110.
- `7c66ed46`: peaks at `PEAK_MIN=0.20` are `[(20, 0.20), (29, 0.23), (115, 0.22)]`. At `PEAK_MIN=0.10` the peak list extends to a structured set including `(9, 0.17), (18, 0.19), (29, 0.23), (39, 0.14), (49, 0.12), (86, 0.16), (106, 0.13), (115, 0.22)` — a candidate fundamental near lag 9–10 with harmonics, or near 29 with `115 ≈ 4 × 29`. The strongest peak is at lag 29 (acf 0.23).
- `4e26d572`: peaks at `PEAK_MIN=0.20` are `[(57, 0.23)]`, extending to `[(57, 0.23), (114, 0.10), (116, 0.16), (172, 0.13)]` at `PEAK_MIN=0.10`. The lags 114 / 116 / 172 cluster near `2 × 57` and `3 × 57`, suggestive of a fundamental at lag 57 with weak harmonics.

The structure is too weak to clear the `PEAK_MIN = 0.30` threshold. Lowering the threshold would bring in false positives on Cluster A (whose smooth-decay acf still clears 0.10 at low lags but is not periodic), so the current convention preserves correctness at the cost of flattening Cluster B into NOPERIOD. The audit script provides the tooling to surface Cluster B's sub-structure on demand without changing the default.

### Convention status

`PEAK_MIN = 0.30` and `LAG_MAX = 128` are preserved. The convention shift from N1 (argmax-in-window) to N1.5 (strict-local-max) was the load-bearing change; thresholds within the new convention are now confirmed appropriate against the substrate. No catalog change. NOPERIOD remains a single tag; the within-NOPERIOD A-vs-B substructure is documented here and accessible via `noperiod_audit.py` if downstream work needs it.

### Bearing on N2 candidate selection

Cluster B's bimodal H profile has direct consequence for N2: the principled candidate list (lowest `gap_over_H` positions in the deep window) will preferentially pick Cluster B's spike events — the rare high-uncertainty positions where the model is briefly wide-open inside an otherwise super-committed trajectory. The N1.5 catalog already showed `48a13037` topping the highest-H baseline at H = 4.68; the audit confirms the spikes are isolated rather than part of a periodic cycle. A clean N2 question opens up: does perturbing at a Cluster B spike redirect the surrounding super-committed trajectory, or does the structure re-converge as if the spike were memoryless? The answer is informative either way — re-convergence would be a strong signature of a stable absorbing region whose boundary the spike briefly touches; redirection would mean the spikes are leverage points the trajectory is locally sensitive to.

Cluster A specimens are uninteresting under either selection rule (gap_over_H is uniformly high; H is uniformly low). They are honest absorbing regions with no within-trajectory perturbation surface; for N2 they would serve as the "boring baseline" against which Cluster B's leverage is measured.

### Follow-ups

- **N2 design pass.** Cluster A vs Cluster B distinction matters for candidate selection. The principled candidate list lands in Cluster B by construction; baseline picks should include both Cluster A specimens (memoryless control) and SCAFFOLD specimens (no-leverage-by-construction control).
- **Sub-tag consideration.** If downstream work makes the within-NOPERIOD distinction load-bearing — e.g. N2 results show Cluster B and Cluster A respond differently to perturbation — a sub-tag like `NOPERIOD-SPIKE` (bimodal H with sub-threshold peaks) vs `NOPERIOD-SMOOTH` (monotonic acf decay, no structure) would earn its keep. The audit script's diagnostics are the operational definition. Not landed pre-emptively.
- **The Cluster B / SCAFFOLD-with-soft-phases similarity.** Both have super-committed positions punctuated by lower-commitment positions. SCAFFOLD has the structure repeating at a period; Cluster B has spike events at quasi-periodic intervals too weak to register. Worth a side-by-side comparison if N2 finds them responding similarly to perturbation — they may be points along a continuum of "structured commitment with rare uncertainty" rather than separate phenomena.

