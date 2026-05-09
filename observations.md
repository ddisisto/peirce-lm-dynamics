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

