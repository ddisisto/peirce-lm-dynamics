# Peirce — Roadmap

*Forward sequence of branches and milestones leading to the next data run. Companions: [brief.md](brief.md) for the shape of inquiry and Cycle 1's conceptual moves; [observations.md](observations.md) for commit-pinned empirical findings; [basins.md](basins.md) for the basin catalog. Updated when a step closes or its scope changes.*

*Status: 2026-05-05. Cycle 1 mid-flight. Selection-bias probe at L_arch closed (catalog v0.3, fp32); persistence layer merged (`6245a01`); project default now fp16. Basin detection v2 is the singular substantive in-flight design direction. One sequential branch stands between current state and the next data run.*

---

## Current position

Main is at `6245a01` (merge of PR #1 from `persistence`): persistence layer landed (trajectory/observation split keyed by content-addressed hashes, KV-cache prefill, runner). `data/peirce.db` carries 100 broad-shallow + 100 selection-bias observations under fp16. Catalog v0.3 frozen as fp32 record; aggregate fp32→fp16 deltas captured in observations.md `2026-05-05` entry.

## Branch sequence to next data run

### 1. ~~`persistence`~~ — closed (`6245a01`)

Persistence layer (trajectory/observation split, prefill-extension, runner) merged. Dense-records lensing capability available — exploratory v2 design can iterate against persisted data rather than re-running the model. Project dtype landed at fp16 alongside the merge.

### ~~2. `design-reqs-refactor`~~ — dropped

The originally-planned step was to refactor the design-reqs surface to align with the post-persistence implementation. Dropped after persistence merge: most of what v2 design needed from design-reqs is settled in code (records / store / runner shape, predicate spec, identity scheme), and the rest are *v2's questions to answer* not pre-answered specifications. The per-path `peirce/CLAUDE.md` + `scripts/CLAUDE.md` + well-named code carry the load that design-reqs refactor would have. brief.md and the design-reqs surface are held as historical (staleness-marked) until subsumed by the catalog-as-data-source rework or until a concrete need forces the touch.

### 2. `basin-v2` (planned, next)

Designs and implements basin detection v2 — entropy-floor / logit-gap-floor probe targeted at the 37 transient trajectories from the fp16 selection-bias run (39 in fp32; persistence-merge produced 37). Calibration distribution: the v0.3 catalog (confirmed positives, fp32) plus the captured fp16 ensemble (confirmed positives, fp16) and the 37 fp16 transients (candidate positives). The pre-design probe — load captured trajectories and the 37 transients from `data/peirce.db`, plot (late-H, late-gap) distributions across window sizes — happens early on this branch using the persistence layer.

Open design questions named for resolution on this branch:

- **Detector signal.** Single statistic (entropy floor or gap floor), combination, or multi-feature classifier? The calibration plot is the pre-design data.
- **Basin identity for non-cyclical basins.** Tail-content fingerprint vs structural pattern signature vs flag-only (catalog stays cycle-only, v2 captures attach a flag without basin-relating). Shapes what coalescence means in v2.
- **Runtime cutoff vs post-hoc classification.** Probe-only mode (run to L_arch, classify post-hoc) is safer for the first v2 run; predicate mode is the optimization once false-positive surface is mapped.
- **Separator vs basin within enumerations.** Period structure inside `(636) (637) (638)` may be detector-visible at the gap-floor level too. Whether v2 fires on the enumeration as a whole or on separators within depends on window placement.

- **Exit criteria:** v2 detector implemented; calibration write-up in observations.md pinned to a commit; basins.md schema extended or ratified as cycle-only per the basin-identity choice the calibration data forces.

### 3. Next data run

Repeat the selection-bias structure on the 37 fp16 uncaptured trajectories with v2 detection / predicate in place, alongside v1. Same model, same initial conditions, same depth budget; the additional capture comes from v2. Generates the next observations.md entry and a v0.4 catalog refresh (fp16-derived). The catalog itself may be re-invented as a query over the persisted store as part of this step. This milestone closes the v1-detection-only era and re-engages the empirical loop.

## Beyond Cycle 1

Out of scope for this roadmap; named in [brief.md](brief.md) *Looking beyond the first cycle* and in [ideas.md](ideas.md). Naturally next cycles include T>0 perturbation, sliding-window inference variants, cross-model comparison, and vocab-exhaustive ensembles. A new ROADMAP iteration begins when the v2 data run lands and Cycle 1's primitives are stable enough to commit to a Cycle 2 frame.
