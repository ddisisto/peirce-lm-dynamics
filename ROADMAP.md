# Peirce — Roadmap

*Forward sequence of branches and milestones leading to the next data run. Companions: [brief.md](brief.md) for the shape of inquiry and Cycle 1's conceptual moves; [observations.md](observations.md) for commit-pinned empirical findings; [basins.md](basins.md) for the basin catalog. Updated when a step closes or its scope changes.*

*Status: 2026-05-05. Cycle 1 mid-flight. Selection-bias probe at L_arch closed (catalog v0.3); basin detection v2 is the singular substantive in-flight design direction. Three sequential branches stand between current state and the next data run.*

---

## Current position

Main is at `212c086`: brief v0.5, catalog v0.3, top-level CLAUDE.md, engine-perf merged (records / engine reshaped for trajectory packets, KV cache threaded, structural-only cycle finder lifted out of `detect_tail_cycle`). The `persistence` branch is one commit ahead of main with the persistence layer staged for merge.

## Branch sequence to next data run

### 1. `persistence` (in flight)

Lands the persistence layer (trajectory/observation split, prefill-extension, runner) on top of the merged engine-perf work. Implementation driven from session "persistence". On merge, the dense-records lensing capability becomes available — exploratory v2 design can iterate against persisted data rather than re-running the model.

- **Prerequisite for:** all subsequent steps. Design-reqs refactor needs the new packet shape settled; basin v2 design needs lensing-against-persisted-data.
- **Exit criteria:** persistence layer merged; one selection-bias-equivalent run captured to disk that can be re-loaded for analysis.

### 2. `design-reqs-refactor` (planned, after `persistence` merges)

Refactors the design-reqs surface to align with the implementation as it actually landed: trajectory packets per design-reqs-records, persistence as first-class, probes architecture. Driven from a dedicated session "design-reqs-refactor". Subdir likely with its own README.md and CLAUDE.md following the discipline established in `212c086`.

- **Prerequisite for:** basin v2 design — v2 wants the records / probe architecture stable to design against.
- **Exit criteria:** design-reqs.md and companions reflect the post-persistence implementation; cross-references between docs and code accurate; brief.md trimmed of implementation-drift content now living elsewhere.

### 3. `basin-v2` (planned, after `design-reqs-refactor` merges)

Designs and implements basin detection v2 — entropy-floor / logit-gap-floor probe targeted at the 39 transient trajectories from the selection-bias probe. Calibration distribution: the v0.3 catalog (confirmed positives) and the 39 transients (candidate positives). The pre-design probe — load v0.3 basins and the 39 transients, plot (late-H, late-gap) distributions across window sizes — happens early on this branch using the persistence layer.

Open design questions named for resolution on this branch:

- **Detector signal.** Single statistic (entropy floor or gap floor), combination, or multi-feature classifier? The calibration plot is the pre-design data.
- **Basin identity for non-cyclical basins.** Tail-content fingerprint vs structural pattern signature vs flag-only (catalog stays cycle-only, v2 captures attach a flag without basin-relating). Shapes what coalescence means in v2.
- **Runtime cutoff vs post-hoc classification.** Probe-only mode (run to L_arch, classify post-hoc) is safer for the first v2 run; predicate mode is the optimization once false-positive surface is mapped.
- **Separator vs basin within enumerations.** Period structure inside `(636) (637) (638)` may be detector-visible at the gap-floor level too. Whether v2 fires on the enumeration as a whole or on separators within depends on window placement.

- **Exit criteria:** v2 detector implemented; calibration write-up in observations.md pinned to a commit; basins.md schema extended or ratified as cycle-only per the basin-identity choice the calibration data forces.

### 4. Next data run

Repeat the selection-bias structure on the 39 uncaptured trajectories with v2 detection / predicate in place, alongside v1. Same model, same initial conditions, same depth budget; the additional capture comes from v2. Generates the next observations.md entry and a v0.4 catalog refresh. This milestone closes the v1-detection-only era and re-engages the empirical loop.

## Beyond Cycle 1

Out of scope for this roadmap; named in [brief.md](brief.md) *Looking beyond the first cycle* and in [ideas.md](ideas.md). Naturally next cycles include T>0 perturbation, sliding-window inference variants, cross-model comparison, and vocab-exhaustive ensembles. A new ROADMAP iteration begins when the v2 data run lands and Cycle 1's primitives are stable enough to commit to a Cycle 2 frame.
