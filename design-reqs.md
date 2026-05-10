# Peirce — Design Requirements

*Substrate stated as given. Orientation for Cycle-2 work. Implementation surface is described authoritatively by `peirce/README.md` and `scripts/README.md`; this document specifies what the substrate is and how Cycle-2 work relates to it.*

*Status: Cycle 2. Revisable; revisions are recorded. The Foundations are supreme — conflicts between this document and `foundation.md` are resolved by either revising this document or initiating a re-founding cycle.*

---

## What this document is

The Foundations specify what the project studies and the frame it studies through. This document specifies what currently exists as substrate, what shape primitives are computed over it, and how Cycle-2 work is scoped against it.

The implementation surface is not duplicated here. `peirce/README.md` describes the package (records, engine, predicates, store, runner, basins probe). `scripts/README.md` describes the runs and smoke tests. Those documents are authoritative for the live implementation; this one describes the substrate at the level of contract, and is touched when contract-level decisions shift.

Sub-READMEs and this document want a review pass before and after substantive implementation work, so contract and implementation stay aligned.

## Substrate (given)

The Cycle-1 substrate is the read-only trunk that Cycle-2 work extends. It comprises:

- **Model.** EleutherAI/pythia-1b-deduped, fp16, CUDA. Stack identity (model + revision + dtype + device + library versions + deterministic flags) is part of every trajectory's identity and recorded in the manifest.
- **Initial conditions.** BOS-only (`<|endoftext|>` id 0) with a single `Injection` at position 0 selecting the branch token. The first cycle materialised the top-100 from the BOS distribution under this convention.
- **Inference.** Hard-cap, T=0 argmax. Trajectories grow monotonically until a terminal-event predicate fires or the architectural context length L_arch=2047 is reached. Sliding-window strategies and T>0 sampling are deferred to later cycles.
- **Persistence.** Content-addressed store at `data/peirce.db`. Two-hash identity: `trajectory_id = hash(stack, initial_ids, injections)`, `observation_id = hash(trajectory_id, predicates, inference_strategy)`. Trajectories are extensible (KV-prefill from existing steps + incremental stepping); observations are write-once. Re-running a script is idempotent.
- **Predicate set.** `eos`, `budget_cap`, `window_cap` from `peirce.predicates`. The C1 substrate also carries `basin_capture` terminal-event tags on observations produced by retired runs (`broad_shallow`, `selection_bias`); the predicate implementation is preserved at git tag `v0.1-final` and removed from the live module surface. Terminal-event tags persist on observations as a record of where the predicate fired, not as a population label or basin classification. New C2 runs use only `eos` / `budget_cap` / `window_cap`; a C2-appropriate replacement (a slot-completion probe, or another shape-aware terminator) is introduced if and when a C2 move warrants one.
- **Materialised depth.** All 100 trajectories are extended to L_arch=2047. The depth window `[1024, end)` is the conventional "deep window" over which shape metrics are computed.

Cycle-2 work treats this substrate as fixed input. Re-running C1 scripts cache-hits. The inheritance is at the *trajectory* level (the `(stack, initial_ids, injections)` tuples and their materialised steps); C2 *observations* are new from here by construction — any C2 inference run produces new observation rows under new predicate sets or new injections, leaving the C1 observation rows preserved as historical record. The two-hash identity makes this clean: trajectory rows cache-hit when re-encountered; observation rows are write-once and accumulate.

## Shape primitives

The per-step record (specified in `peirce/records.py`) carries six fields per step: chosen token (id + decoded), log-probability of chosen, distribution entropy, most-probable non-chosen alternative (id + decoded), alternative probability, rank-1/rank-2 logit gap. These fields are the substrate over which all downstream shape work is computed.

Per-trajectory **shape metrics** computed over the deep window:

- **`onset`** — first position holding entropy below 0.1 for 8 consecutive steps. A collapse-speed scalar.
- **`floor_H`, `floor_gap`** — median entropy and median rank-1/rank-2 logit gap over the deep window. Position-along-the-(H, gap)-manifold scalars.
- **`osc_amp`** — standard deviation of entropy over the deep window. Oscillation-amplitude scalar; the simplest quantity that distinguishes flat from cycling attractors.
- **`peaks`** — local maxima of the normalized autocorrelation of mean-subtracted deep-window entropy in `[lag_min, lag_max]` above `peak_min`, ordered by lag. The full period-structure measurement; clean periodic signals show a harmonic ladder at multiples of the fundamental, multi-period or sub-period structure shows non-multiple lags, NOPERIOD signals return `[]`. The empty list when signal variance is below noise.
- **`period`** — single-integer convention over `peaks` for renderers and downstream consumers that need one. Current convention: smallest divisor of the strongest peak that is itself in the peak list; falls back to the strongest peak when no in-list divisor is found. Convention resolves harmonic aliasing (clean ladders) and avoids misreading sub-periodicities (peaks at lags that don't divide the fundamental). Convention is revisable; specimens where the convention disagrees with reasonable alternatives are surfaced by inspection of `peaks`.
- **`gap_over_H`** — `floor_gap / max(floor_H, ε)`. Commitment ratio at the floor; informative-but-tightly-coupled to the (H, gap) manifold.

Specific metric definitions are revisable. The umbrella commitment — that shape (the structure of the per-step timeseries) is the primary taxonomic surface — is foundational. The promotion of `peaks` to a primitive and demotion of `period` to a flagged convention reflects the discipline of measurement-as-measurement: where a single-int aggregate hides structure that the underlying measurement preserves, the underlying measurement is the contract and the aggregate is the convention.

The (H, gap) per-step relationship across the substrate sits on a 1-D manifold; what carries information is position along the manifold over time, not the (H, gap) coupling itself. `osc_amp` is the simplest scalar capturing motion along the manifold.

## Within-attractor vocabulary

`foundation.md` defines **phase position**, **slot**, **scaffolding**, and **slot-readout** for attractors with template structure. Reproduced here for proximity rather than re-derivation: a phase position is one of the periodic positions in the cycle of an attractor with template structure; a slot is a phase position whose chosen-token distribution across recurrences is non-degenerate; scaffolding is the rest; slot-readout is the descriptive operation of reading a slot's alt-token distribution across recurrences as the model's local prior over the slot's class.

This vocabulary is the bridge between shape-level metrics (computed over the deep window without reference to template structure) and within-attractor structure (computed once cycle period is known and the attractor's phases can be partitioned).

## Descriptive script set

Read-only renderers over the persisted substrate; no model load, no inference:

- `scripts/plot_trajectories.py` — matplotlib renderings under `data/plots/`. Per-trajectory shape metrics over the deep window; aggregate, shape-axis, outlier, and grid panels.
- `scripts/high_h_readout.py` — top-N highest-entropy positions per trajectory in the deep window, with chosen / alt / context tokens. The descriptive half of the slot-readout operation.

The smoke tests (`smoke_engine`, `smoke_kv_parity`, `smoke_store`) and the substrate-building run (`full_depth_extension` — top-K BOS × L_arch under `[eos, window_cap]`, the runnable spec of substrate construction) are described in `scripts/README.md`. Cycle-2 read-only descriptive work extends this set; Cycle-2 inference work extends `scripts/` with new runs that use `runner.observe(...)` and persist to the same store.

## Cycle-2 scope

The first cycle's working shape was **broad-shallow → representative-deep → non-branching extension**: select 100 starts, materialise each to L_arch as a single trajectory, observe what shape they took. The substrate that produced is the trunk.

Cycle 2 holds the trunk read-only and works as **in-fill via branching**. The C1 in-fill explored *which trajectories to produce* under non-branching extension; C2 explores *the branches off existing trajectories* — alternate-path continuations from selected positions on the 100, complemented by seeded class-enumeration probing. Both interesting positions (high-H slots, transient-leverage points) and baseline non-interesting positions (for control) are in scope; partitioning by what the substrate's shape signals is the entry point.

The forward sequence of Cycle-2 moves is carried inline in `CLAUDE.md` rather than this document, because it shifts faster than the substrate contract and benefits from being in primary context for every session.

## Cycle-to-cycle inheritance

In-cycle catalogs are designed to outlast the cycle. The expectation is that Cycle 3's substrate is C2's catalog of record — the consolidated descriptive readout under v0.2 vocabulary — the way C2's substrate is C1's trajectories. Build accordingly. Catalogs are constructed over substrate primitives that are foundation-stable (per-step records, shape metrics computed over them, empirical distributions at structural positions), not over the current cycle's regime taxonomy or working-vocabulary classifications. A catalog should remain legible after a re-founding that retires the vocabulary it was first read in; if a catalog requires the cycle's regime names to interpret its rows, that's a signal it's classifying rather than describing, and the failure mode the discipline guards against.

## Regime vocabulary

The C2 catalog of record (`scripts/shape_catalog.py`) emits regime tags from the substrate's own shape signals — autocorrelation peaks of the deep-window H-trace, chosen-token entropy across recurrences at each phase position, delta-evidence on slot chosen sequences. Those tags are canonical:

- **`SLOTTED`** — detectable period; at least one phase position whose chosen-token distribution across recurrences is non-degenerate (a *slot*, in `foundation.md` vocabulary). Sub-tags differentiate the slot's chosen-sequence character: **`SLOTTED-CLASS`** (chosen rotates through a class with non-trivial alt-distribution density), **`SLOTTED-COUNTER-INT`** (consecutive integer counter at high match-fraction), **`SLOTTED-COUNTER-LETTER`** (consecutive letter counter), **`SLOTTED-MIXED`** (slotted with both class-slot and counter-slot phases coexisting). Counter-vs-class is a tagging heuristic at current N (6 + 1 of 17 SLOTTED specimens carrying a counter sub-tag); the underlying delta-evidence (median chosen-sequence delta, match-fraction) is reported alongside, so the tag is descriptive at this scale, not classificatory.
- **`SCAFFOLD`** — detectable period; every phase position is pinned (chosen token fixed across recurrences). The trajectory is a clean repeating cycle with no within-cycle slack.
- **`NOPERIOD`** — no detectable period in the autocorrelation of the deep-window H-trace under current convention (strict local maxima above `PEAK_MIN` in lags `[LAG_MIN, LAG_MAX]`).

### Precedent

Both Markov-chain framings of LM dynamics in the surveyed neighbourhood (Geng et al. 2603.11228, Zekri et al. 2410.02724) stop at "the chain has entered a recurrent set" without decomposing within-cycle structure. The slot/scaffolding axis on which `SLOTTED` and `SCAFFOLD` are partitioned is project-distinctive — no surveyed work names it. The standalone precedent review at [`reports/regime-vocab-precedent.md`](reports/regime-vocab-precedent.md) (read pinned to commit `4309b3e`, report itself committed at `f7cc476`) extracts terminology, formalisation scope, and within-cycle treatment from both papers section-by-section; the original survey at [`lit-review.md`](lit-review.md) carries an addendum noting the canonisation pass.

The *coarse* axis is well-known and is credited explicitly:

- **`SCAFFOLD-period-1`** at the per-token level is — under Zekri's token-level transition kernel `Q_f` — a Markov-chain fixed point. The alias is near-identical, not just analogous: the trajectory's repeating state is one with `Q_f` self-transition under deterministic decoding, which is the textbook fixed-point definition at that abstraction.
- **`PERIODIC` vs `NOPERIOD`** (the umbrella distinction over `SLOTTED` ∪ `SCAFFOLD` vs `NOPERIOD`) is conceptually adjacent to Geng's "fixed point or short cycle" vs "long pre-recurrence phase" and Zekri's "in recurrent class" vs "in transient class / slow mixing". Granularity differs (sentence-level vs per-token; first-recurrence-time and mixing-time vs autocorrelation-period), so the alias is conceptual rather than identical.

Names that would imply Peirce introduced "trajectories enter cycles" are avoided; the cycle phenomenon is well-established Markov-chain content. The project's contribution is the within-cycle decomposition, and the canonical tags reference it directly without coining genre-labels for the umbrella phenomenon.

### Period and attractor — three-way ambiguity

"Period" carries three distinct meanings in the surveyed neighbourhood:

1. **Markov-chain period** — gcd of return times to a state. Zekri's chain is aperiodic-by-construction (via the deletion process), so this is trivially 1 throughout their analysis.
2. **Dynamical-systems period** — cycle length under iteration. Geng's "2-cycle" example is at this granularity, on sentence-level state.
3. **Peirce's period** — autocorrelation peak of the deep-window H-trace, in lags `[LAG_MIN, LAG_MAX]`. The flagged-convention treatment in the shape-primitives section above (`peaks` as primitive, `period` as convention layer) handles the ambiguity within the project; readers crossing in from either Markov-chain meaning should not conflate.

"Attractor" carries similar ambiguity: Wu et al. 2502.15208 uses "attractor cycle" centrally for iterated-paraphrasing; Geng uses it twice as decoration on "recurrent class"; Zekri does not use the term; `foundation.md` defines it as a region of phase space that trajectories enter and remain in. The project's own use is well-grounded; the granularity (per-step T=0 self-conditioning under fixed initial condition) is what positions it against the neighbours.

### Forward thread

Ivgi et al. 2407.06071 ("From loops to oops: fallback behaviors of language models under uncertainty") — cited by Zekri as the in-practice repetition reference — is flagged as a possible finer-grained precedent. Pre-cleared by hand as conceptually overlapping at coarser granularity than the slot/scaffolding decomposition, not pressing for the canonisation; carried as a future precedent pass and parked in `ideas.md`.

## Foundations supremacy

No requirement in this document and no implementation choice overrides `foundation.md` without a deliberate re-founding cycle. Where this document and the implementation surface in `peirce/README.md` / `scripts/README.md` drift apart, the drift is itself a signal — to refresh the substrate-as-given, or to escalate a contract-level decision.

---

*This document assumes familiarity with `foundation.md` (vocabulary and frame), `peirce/README.md` (package surface), and `scripts/README.md` (runs and smoke tests). The forward sequence of Cycle-2 moves is in `CLAUDE.md`.*
