# Peirce — Observations (Cycle 2)

*Append-only commit-pinned log of empirical findings. Each entry pins to a commit hash and includes the run command(s) needed to reproduce. Scripts can evolve or die; entries reproduce from the commit they pin.*

*Cycle 1 entries: see [`archive/observations-cycle-1.md`](archive/observations-cycle-1.md) (preserved in full; reproducible from commits at or before the `v0.1-final` tag).*

---

## 2026-05-09 — N1 first-light: slot/scaffolding decomposition over the 100-trajectory substrate

**Commit:** `8631813`
**Run:** `uv run python scripts/phase_aware_chosen.py`
**Config:** read-only over `data/peirce.db`. 100 fp16 selection-bias observations, deep window `[1024, end)`, period detection via autocorrelation peak in lag ∈ `[2, 128]` with `peak_min = 0.3`, slot threshold `chosen-token H > 1e-3` nats.

### Headline

The slot/scaffolding decomposition over the substrate produces a clean three-way partition: 19/100 trajectories have at least one slot, 78/100 have a detected period but no slots (every phase pinned to a single chosen token across recurrences), 3/100 have no detected period. Within the 19 slotted trajectories, a sub-partition not anticipated by the project's vocabulary surfaces immediately: **counter slots** (chosen tokens enumerate consecutive integers / alphabet letters across recurrences, mechanical successor) versus **class slots** (chosen tokens rotate over a small semantic class). One textbook class-slot specimen — `e1069ae4`, period 43, single slot at phase 0 emitting ` first`/` second` with empirical alt-distribution including ` contact` — proves the slot-readout operation works as the foundation predicts.

### Aggregate counts

- **SLOTTED** (≥1 phase with chosen-token Shannon entropy > 1e-3 nats across recurrences): 19/100
- **SCAFFOLD-only** (period detected, every phase chosen-pinned): 78/100
- **NOPERIOD** (no autocorrelation peak ≥ 0.3 in lag window): 3/100

### Proof-of-concept class slot

- **`e1069ae4`** — period=43, floor_H=0.0047, osc_amp=0.2211, slots=1/43.
  - phase=0, n_recur=24, chosen_H=0.679 nats (≈ ln(2)).
  - chosen distribution: ` first`×14 (0.58), ` second`×10 (0.42).
  - alt distribution: ` second`×12 (0.50), ` first`×9 (0.38), ` contact`×3 (0.12).

The chosen distribution is binary; the alt distribution is the chosen distribution swapped (each recurrence's runner-up is the other slot member) plus a third token, ` contact`, never picked but flagged as alt 3 times. Reading ` contact` as the model's pulled-aside third candidate gives a non-trivial datum about the model's local prior over this slot's class — exactly the readout the project's vocabulary names.

### Counter slots — an unexpected sub-class

Specimens whose slot chosen-tokens form a successor sequence (consecutive integers, alphabet letters), not a discrete class:

| oid | period | slots | slot phase | chosen sample | n_recur | chosen_H |
|---|---|---|---|---|---|---|
| `e1afc61b` | 29 | 1/29 | 18 | `'36','37','38','39','40','41',…` | 35 | 3.555 |
| `d58ffabc` | 22 | 1/22 | 4 | `' 40',' 41',' 42',' 43','44',…` | 47 | 3.850 |
| `f008f7d2` | 19 | 1/19 | 9 | `'r','s','t','u','v','w','x',…` | 54 | 3.251 |
| `7b1005ae` | 7 | 1/7 | 2 | `'147','148','149','150','151',…` | 146 | 4.984 |

These are real slots under the chosen-H criterion but the "class" being read out is "successor of the previous recurrence's emission." Mechanism is plausibly induction-head copy + increment, distinct from the FV-head class-conditioned-generation hypothesis the project's class-enumeration framing implies. The vocabulary should distinguish: the slot-readout *operation* is the same (alt distribution at the slot phase), but the *interpretation* of the readout differs sharply between counter and class cases. A counter slot's alt distribution is dominated by neighbours-of-the-counter-value (` 45`×2, ` 50`×2, ` 53`×2 at d58ffabc's slot) rather than alternative class members.

### Period-detection harmonics: `slots = N / N` specimens

Seven specimens come up as SLOTTED with every phase a slot and uniform chosen_H values (0a4614cd, 08142fe5, 6c5f90d9, ed25bd71, fe863662, a661c8ae, 62498529). Inspection of the first specimen (`0a4614cd`, period=96, slots=96/96, all phases chosen_H=1.768 nats ≈ ln(6)) shows the chosen distributions across phases are rotations of the same six-token set. This is a period-detection-aliasing signature: the true cycle period is an integer divisor of 96, and `dominant_period`'s argmax-in-`[2, 128]` logic picked the harmonic. The current `dominant_period` returns `argmax(autocorrelation[lag_min:lag_max+1])` — *highest* peak in the window, not *first* peak above threshold. Fix is to switch to first-peak-above-threshold; touches `scripts/plot_trajectories.py` (where the function originates) and N1 (which currently inherits the bug). Records the issue here rather than fixing in the same step because the substrate-shape-metric `period` is a contract-level quantity and the fix should propagate consistently.

### Single-mode template cycles (high-osc-amp SCAFFOLD specimens)

The SCAFFOLD bucket is internally heterogeneous. High-osc_amp specimens like `d8e73c51` (period=116, osc_amp=0.3841), `fe8a36a8` (period=25, osc_amp=0.2530), `134c9875` (period=26, osc_amp=0.1657) have detected periods, every phase pinned, and substantial within-cycle entropy oscillation. The trajectory repeats a fixed token-template; some positions in the template are naturally higher-H than others (the model has rotational potential there) but always commits to the same token. This is the textbook single-mode-template-cycle / R2 specimen. Compare to slotted specimens at similar osc_amp (`e1069ae4` osc_amp=0.2211, `e1afc61b` osc_amp=0.3120): the *shape* of the entropy oscillation is similar, but only the slotted specimens actually rotate the chosen token at the high-H phases.

### NOPERIOD specimens — three trajectories

- `1453d66b`: floor_H=0.0012, osc_amp=0.4071 (highest osc_amp in the entire substrate)
- `05677c58`: floor_H=0.0018, osc_amp=0.1055
- `11b07bda`: floor_H=0.0016, osc_amp=0.0809

These have measurable entropy oscillation but no autocorrelation peak ≥ 0.3 in the search window. Not single-mode cycles (osc_amp too high). Not phase-partitionable by N1 (no period). These need a different tool — drifting / quasi-periodic / multi-period analysis. The `1453d66b` specimen having both the lowest floor_H and the highest osc_amp in the substrate is the kind of edge case worth singling out for direct trajectory inspection.

### Follow-ups

- **Period-detection refinement.** Switch `dominant_period` from argmax to first-peak-above-threshold; promote to `peirce/shape.py` once a third consumer warrants it. Re-run N1 + `plot_trajectories.py` + `high_h_readout.py` after the change to see the catalog under corrected periods.
- **Counter-vs-class sub-partition.** Either tag this in N1's output (heuristic: are the slot's top chosen tokens lexically/numerically consecutive?) or land it as project vocabulary. The mechanism distinction (induction-head succession vs FV-head class generation) is testable in Pythia by head-ablation, listed under N4 follow-ups in `lit-review.md`.
- **NOPERIOD specimen direct inspection.** Render the deep-window entropy trace and chosen-token sequence for `1453d66b`; ask whether it's drifting (period changes over the window), quasi-periodic, or genuinely aperiodic.
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

- **`e1069ae4`** (textbook class slot): period=43 (prime), peaks=[(43,0.92), (86,0.90)], slot at phase 0, chosen=` first`×14 / ` second`×10, alt=` contact`×3. Recovers N1 first-light reading.
- **`e1afc61b`** (counter slot): peaks include both fundamental at 29 (acf 0.96) and weak sub-periodicity at 7 (acf 0.40); divisor rule correctly returns 29 (29 % 7 ≠ 0). Slot at phase 18, chosen=`36`/`37`/.../`70`, delta evidence median=+1, frac=1.00 → COUNTER-INT. Recovers N1 first-light reading.
- **`134c9875`** (nested 2-and-26): peaks=[(2,0.44),(24,0.44),(26,0.97),(28,0.42),(50,0.43),(52,0.93),...]; divisor rule returns 2 (smallest in-list divisor of strongest=26). Period-2 alternation captures the within-cycle structure cleanly; the 26-period harmonic structure is preserved in the peaks field.
- **`0a4614cd`** (chosen-token / H-trace period divergence): peaks=[(96,0.62)] only. 96/96 slots at chosen_H=1.768 ≈ ln(6) — i.e. 6 distinct tokens rotating across phases. The chosen-token rotation has period 96/6=16, but the entropy timeseries autocorrelation at lag 16 sits below `peak_min=0.3`. The catalog reports the H-trace measurement honestly (no detectable lag-16 peak) and the divergence is visible in the slot-readout (rotation pattern across the 96 phases is the same 6-element class). A real subtlety: chosen-token-rotation period and acf-of-H-trace period can diverge; the catalog doesn't fabricate the rotation period from the chosen tokens.

### SCAFFOLD commitment-strength heterogeneity

Position-resolved gap readouts surface the within-SCAFFOLD heterogeneity. Examples:

- **`d8e73c51`** (period=116, osc_amp=0.3841, peaks=[(116,0.87)] single peak): commit-soft phases at gap_med ≈ 0.27 (chosen=`------`, `~~~`) alongside commit-hard phases at gap_med ≈ 39.75. The trajectory carries a fixed token-template with extreme intra-template commitment variance.
- **`b9cfdf7b`** (period=22, full harmonic ladder peaks=[(22,0.98),(44,0.96),(66,0.94),(88,0.92),(110,0.90)]): one near-bifurcation phase at gap_med=0.469 (chosen=` "`) with the rest at 7+ — a single weakly-committed phase within an otherwise strongly-pinned scaffold.
- **`7dbde4ff`** (period=63 fundamental, peaks include weak side-peaks at lags 2, 61, 65, 126, 128): the side-peaks at 61/65 and 126/128 are 63±2 / 126±2 — period-2 sub-structure interfering with the period-63 fundamental, visible directly in the peak list.

### Counter-vs-class as a description tool

With N=6 COUNTER-INT / N=1 COUNTER-LETTER / N=17 CLASS / N=2 MIXED, the heuristic is descriptive at this sample, not a classifier. The catalog reports the underlying delta evidence (int and letter delta median + match-fraction) under each slot row, so the convention's tag is auditable per-slot. Counter slots in the substrate display essentially perfect arithmetic structure (median delta = +1, match-fraction = 1.00 in the typical case); class slots show no integer or letter consecutivity (delta evidence reads as N/A). The mid-cases the heuristic was designed to surface — partial-counter-with-noise, or class-rotation-that-happens-to-be-numerically-ordered — do not yet appear in the substrate.

### N2 candidate hand-off

The catalog's principled candidate list (lowest gap_over_H positions in the deep window) is dominated by `e1069ae4`'s slot positions (chosen=` first` / ` second`, gap_over_H ≈ 0.0–0.2) — the textbook class-slot's near-bifurcation moments, which is what the principle would predict. The simplest baseline list (highest H positions) tops out at the NOPERIOD specimen `1453d66b` at H=4.68 and the COUNTER-LETTER specimen `f008f7d2`. Both lists ship in the catalog output for N2 to consume.

### Follow-ups

- **NOPERIOD specimen audit.** Now 8 specimens (was 3); the `1453d66b` highest-osc_amp one is still the most interesting. The 5 new NOPERIOD additions are likely monotonically-rising-acf-into-out-of-window trajectories that the strict-local-max rule correctly excludes; worth confirming by inspecting their peak lists (which should be empty under the current threshold) and considering whether a wider lag window or lower peak threshold is warranted for any of them.
- **Counter-vs-class with N=6/17.** The heuristic is descriptive at this sample. Lifting into project vocabulary requires more specimens (or seeded probing under N3) to populate the mid-cases.
- **`0a4614cd` chosen-token-period vs H-trace-period divergence.** The catalog reports both signals honestly but the catalog doesn't currently *name* the divergence. If more such specimens emerge, a named tag (e.g. `SLOTTED-ROTATION-AT-HARMONIC` or similar) may earn its keep.
- **Regime-vocabulary canonisation (`design-reqs.md` "Open: regime vocabulary").** Precondition 1 (mechanical re-derivation from shape signals) is now effectively met by the catalog. Precondition 2 (renaming consideration vs Markov-chain prior art — Geng 2603.11228, Zekri 2410.02724) is the remaining work.

