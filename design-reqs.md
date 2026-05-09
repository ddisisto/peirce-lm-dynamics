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
- **Predicate set.** `eos`, `budget_cap`, `window_cap` from `peirce.predicates`. The C1 substrate also carries `basin_capture` terminal-event tags on observations produced by retired runs (`broad_shallow`, `selection_bias`); the predicate implementation is preserved at git tag `v0.1-final` and removed from the live module surface. Terminal-event tags persist on observations as a record of where the predicate fired, not as a population label or basin classification. New C2 runs use only `eos` / `budget_cap` / `window_cap`; a C2-appropriate replacement (entropy-floor probe, slot-completion probe, or other shape-aware terminator) is introduced if and when a C2 move warrants one.
- **Materialised depth.** All 100 trajectories are extended to L_arch=2047. The depth window `[1024, end)` is the conventional "deep window" over which shape metrics are computed.

Cycle-2 work treats this substrate as fixed input. Re-running C1 scripts cache-hits.

## Shape primitives

The per-step record (specified in `peirce/records.py`) carries six fields per step: chosen token (id + decoded), log-probability of chosen, distribution entropy, most-probable non-chosen alternative (id + decoded), alternative probability, rank-1/rank-2 logit gap. These fields are the substrate over which all downstream shape work is computed.

Per-trajectory **shape metrics** computed over the deep window:

- **`onset`** — first position holding entropy below 0.1 for 8 consecutive steps. A collapse-speed scalar.
- **`floor_H`, `floor_gap`** — median entropy and median rank-1/rank-2 logit gap over the deep window. Position-along-the-(H, gap)-manifold scalars.
- **`osc_amp`** — standard deviation of entropy over the deep window. Oscillation-amplitude scalar; the simplest quantity that distinguishes flat from cycling attractors.
- **`period`** — dominant lag from autocorrelation of mean-subtracted deep-window entropy; `None` when variance is below noise.
- **`gap_over_H`** — `floor_gap / max(floor_H, ε)`. Commitment ratio at the floor; informative-but-tightly-coupled to the (H, gap) manifold.

Specific metric definitions are revisable. The umbrella commitment — that shape (the structure of the per-step timeseries) is the primary taxonomic surface — is foundational.

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

## Open: regime vocabulary

Cycle 1 surfaced a provisional three-regime split among attractor types observable at depth (recorded in `archive/cycle-1-findings.md`). Of that split, the **slot / scaffolding / slot-readout / class-enumeration-attractor** vocabulary is retained going forward — supported by the literature survey at [`lit-review.md`](lit-review.md), which identifies this neighbourhood as project-distinctive (no surveyed work partitions degenerate regimes by within-cycle template structure or treats high-H phase-position alt distributions as recoverable class priors).

The Cycle-1 sub-regime names *pinned cycle* (R1) and *mode-locked structural attractor* (R2) are deliberately not lifted forward, pending two preconditions:

1. **Mechanical re-derivation.** The C2 phase-aware chosen-token analysis (forward-sequence move 1 in `CLAUDE.md`) produces per-attractor regime tags from the substrate's own shape signals — chosen-token entropy across recurrences at each phase position. The output of that analysis is what re-enters the working vocabulary as canon, not the by-eye provisional partition.
2. **Renaming consideration.** The literature survey notes that these sub-regimes are sub-cases of greedy-decoding fixed-point / short-cycle behaviour already known in the Markov-chain literature (Geng et al. 2603.11228, Zekri et al. 2410.02724); the names that survive into canon should reference the within-cycle distinction property directly (e.g. *single-mode cycle* / *single-mode template cycle*) rather than coining genre-labels that imply Peirce introduced the cycle phenomenon.

When both preconditions are met, regime vocabulary lands in `observations.md` (per-attractor entries) or a successor `basins.md` (catalog form), with this document updated to point at the canonical naming.

## Foundations supremacy

No requirement in this document and no implementation choice overrides `foundation.md` without a deliberate re-founding cycle. Where this document and the implementation surface in `peirce/README.md` / `scripts/README.md` drift apart, the drift is itself a signal — to refresh the substrate-as-given, or to escalate a contract-level decision.

---

*This document assumes familiarity with `foundation.md` (vocabulary and frame), `peirce/README.md` (package surface), and `scripts/README.md` (runs and smoke tests). The forward sequence of Cycle-2 moves is in `CLAUDE.md`.*
