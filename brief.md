# Peirce — Project Brief

*Companion to the [Foundations](foundation.md), [Design Requirements](design-reqs.md), [Records Design](design-reqs-records.md), and [Steered Trajectories Design](design-reqs-steering.md). Reads alongside [observations.md](observations.md) (empirical observations, commit-pinned) and [ideas.md](ideas.md) (forward-looking threads not yet ready for design surfaces). Maps the shape of inquiry across cycles, and the first cycle's concrete moves.*

*Status: v0.4 (2026-05-01). Cycle 1 mid-flight: Phases 0–2 closed at small scale; basin detection v1 and the catalog (v0.2) are formalized; runtime basin-capture predicate is live. Phase 3 (in-fill) is active, with the selection-bias probe and basin-detection v2 as the in-flight directions. The brief is more revisable than the requirements and far more revisable than the foundations. Substantial revision is recorded; minor edits are not.*

---

## What this document is

The Foundations specify what the project studies and the frame it studies through. The Design Requirements (and their companions) specify what the system must do and the structural properties it must have. Neither commits to a specific first move. This document does.

The brief maps the shape of inquiry — the recurring pattern by which each cycle produces understanding — and the first cycle's concrete instantiation of that pattern. It is downstream of the Foundations and Requirements; nothing here overrides anything there.

## The shape of inquiry

The project is operationally cartographic. Each cycle maps a region of a multi-dimensional space and earns the right to extend the map.

Axes explored within a cycle:

- **Breadth.** The number of trajectories sampled at a given branching point, parameterized by k. At step 0 from `[BOS]`, k ranges from 1 (the model's argmax start) to |V| (every token in the vocabulary). Small k covers the most-probable, in-distribution starts; large k progressively reaches OOD territory.
- **Depth.** The number of steps the trajectory is observed for, bounded above by L_arch under hard-cap inference. Within hard-cap at T=0, depth-given-start is deterministic, so depth is an analysis parameter — how far one chooses to look — rather than a generation parameter.
- **Temperature.** T=0 is the first-cycle baseline. T>0 produces stochastic trajectories and is named as the natural axis for the first major perturbation cycle; the kernel formulation accommodates it without architectural change.

Axes that index *which cycle of work you are in*:

- **Inference strategy.** Hard-cap is the assumption-free baseline. Sliding variants — naive, attention-sinks, chunked-grain — each shape post-L dynamics differently and each constitute their own cycle of work.
- **Perturbation type.** T>0 is the natively continuous perturbation; token injection and context manipulation are discrete operators on top.
- **Model.** Cross-model comparison earns its keep once the apparatus has been stabilized on one model and produces primitives worth comparing.

Within a cycle, the recurring shape is **broad-shallow → representative-deep → in-fill**. The broad-shallow scan surveys a wide region of breadth at modest depth — enough to surface candidates but not enough to adjudicate them. The representative-deep extension takes selected candidates and runs them out toward L_arch, watching probability dynamics over depth to distinguish true asymptotic structure from extended transients. The in-fill targets regions where the first two passes surfaced something worth understanding more precisely. Each pass is cheap relative to the next; the choice of what to deepen and where to in-fill is itself a finding.

The crystal hypothesis is not directly tested in the first cycle. Crystals, if real, plausibly first appear at depths where local self-loops have either crystallized into true attractors or escaped — which is precisely what the broad-shallow → representative-deep arc is built to distinguish. Earning the right to make a crystal claim is itself part of the work.

## First cycle: instantiation

The first cycle's moves are concrete and bounded. They are chosen to produce something legible to read by hand, on modest hardware, within timescales that allow rapid iteration on what the project is even looking at.

- **Model.** EleutherAI/pythia-1b-deduped. Mature interpretability ecosystem, fully open training data, deterministic-replay infrastructure, comfortable on a GTX 1070 in fp32. Vocabulary 50277, BOS = `<|endoftext|>` (id 0), L_arch = 2048.
- **Initial condition.** `[BOS]` alone, the model's null prompt.
- **Breadth.** Top-100 from `[BOS]`. The 100 most-probable starting tokens cover the bulk of the BOS-conditioned distribution; the OOD tail (positions 101 ... 50277) is named and deferred to later cycles.
- **Depth budget.** 64 tokens per trajectory in the broad-shallow pass — sufficient to surface candidate cycles of moderate period (period < ~20). Selected trajectories are extended toward L_arch in the representative-deep pass. Window-cap at L_arch=2048 is theoretical at this scale; budget-cap is the practical extrinsic terminal.
- **Inference and sampling.** Hard-cap, T=0 argmax. Deterministic given model + start token; no replicates, no seeds, no sampling variance to characterize before the substrate is mapped.
- **Total compute.** 100 trajectories × ≤64 steps = at most 6400 token-steps for the broad-shallow ensemble. Trivial on the 1070.
- **Per-step thin records.** Specified in the [records design](design-reqs-records.md): chosen token (id and decoded), log-prob of chosen, distribution entropy, most-probable non-chosen alternative and its probability, rank-1/rank-2 logit gap. Six fields per step. Trajectory observation packets carry these alongside stack identity, initial condition, predicate set, and terminal event.
- **Storage.** Records held in-memory for the script-driven first-cycle work; selected outputs captured as observation entries in [observations.md](observations.md). Persistence as artifact format is deferred — see *Looking beyond the first cycle*.
- **Candidate-basin recognition.** Manual plus ad-hoc cycle-finding for the small-scale runs. Formalization into a basin-detection probe and a basin catalog is the immediate next priority within Phase 2 — see below.

The smoke test's `'\n' → '\n'` self-loop at step 1 was not assumed to be a true fixed point. Whether the leading-whitespace regime escapes into content — titles, banners, metadata blocks reflected from the training distribution — was among the things the first cycle was set up to find out. Representative-deep extension of that branch (rank 0 in the broad-shallow ensemble) settled into a period-11 phrase basin on entirely different content, validating the depth-as-adjudicator move; the per-step trace is in observations.md.

## Phase 0 — substrate and harness (closed)

Phase 0 closed a small set of decisions and stood up the infrastructure the rest of the cycle depends on.

**Pinned and built.**
- Model: pythia-1b-deduped, fp32, CUDA on GTX 1070.
- Tooling: uv with Python 3.12, dependencies via `uv add`, hatchling build-system so `peirce` installs as an editable package.
- Repo layout: flat package at `peirce/` with `engine.py`, `predicates.py`, `records.py`, `basins.py`. Scripts in `scripts/`. Data artifacts under `data/` (gitignored, currently unused).
- Inference convention: direct token feed (`[BOS, ...]`) with no chat-template wrapper. Sensitivity to plumbing is a finding to characterize, not a problem to eliminate upfront.
- Engine: `generate_trajectory(model, tokenizer, initial_ids, predicates, first_step_override)` returns a `Trajectory` of `StepRecord`s plus a terminal event. Hard-cap T=0 is the default; the architecture accommodates T>0 and step-0 override without modification.
- Predicate framework: `(history, records, n_steps) → tag | None` closures. EOS, budget-cap, window-cap, and basin-capture are the implemented predicates. Adding a new event observer is registering a new predicate.
- Per-step thin records: six fields (chosen token id and decoded, log-prob, entropy, alt-token id and decoded, alt-prob, rank-1/rank-2 logit gap), per the [records design](design-reqs-records.md).
- Basin probe: `peirce/basins.py` carries `detect_tail_cycle(steps, max_period, cycle_window, stats_window) → BasinSignature | None` plus `basin_capture_predicate` that wraps it for runtime use with a K-rep confirmation threshold.
- Smoke test: `scripts/smoke_engine.py` produces a small ensemble from top-5 BOS branches and prints thin records.
- Observation log: `observations.md` is the append-only, commit-pinned record of empirical findings. Basin catalog: `basins.md`, currently at v0.2.

**Carried into Phase 3.**
- `peirce/records.py` rework to fully align with the [records design](design-reqs-records.md) — observation packet structure, windows as first-class objects in code, probes architecture — is deferred until something demands it. The current minimal records (six fields) already carry the analytic and reproducibility instrumentation; the structural rework becomes load-bearing when persistence lands or cross-trajectory probes need a uniform interface.

**Deliberately deferred.**
- Persistence of trajectory artifacts. Trajectories are well-described for inference-time observation, with select outputs captured as observation entries based on the question being asked. Full persistence becomes the right move when `records.py` is sufficiently stable that the schema is unlikely to churn, *or* when persistence blocks something critical (cross-run analysis, basin-coalescence detection across runs, contributor-shareable artifacts). Either condition is the trigger; the format choice (Parquet was the working assumption; Zarr is also in dependencies) is decided then.
- Manifest serialization as a separate module. Stack-identity and run-config metadata travel with each trajectory packet per the records design; a separate manifest module is not load-bearing until persistence lands.
- Dense kernel artifacts. The full vocab × vocab transition kernel at any specific context is computable on demand; storing one is not load-bearing for the first cycle. The single-step view at `[BOS]` is implicitly captured by step 0 of the trajectory ensemble.
- Engine validation against a separately produced dense reference. Closed-form spot-checks against direct logit calls suffice; a dense-artifact phase is not warranted at first-cycle scale.

## Phase 1 — broad-shallow ensemble (closed at small scale)

The 100 × 64 ensemble ran three times: first on 2026-04-30 (commit `3d9d401`) under a manual cycle scan, then on 2026-05-01 (commit `ae95f32`) under a formalized post-hoc probe, then refreshed on 2026-05-01 (commit `08b0ba5`) under the runtime basin-capture predicate. Detailed observations are in observations.md. Headline findings stable across runs: zero EOS within 64 tokens across all 100 starts; clear semantic-attractor patterns at the content level (medical-paper boilerplate, C/C++ headers, JSON-like structures) that token-level cycle detection misses entirely; basin coalescence is real and concentrated in the simplest structural basins.

Primary observables, as exercised:

- Distribution of terminal events: 28/100 captured by the runtime predicate at K=4 reps within 64 tokens; 72/100 reached budget-cap as still-transient; zero EOS.
- Captured-trajectory length distribution: median 13, mean 20, range 4–61. The runtime predicate frees ~44 forward passes per captured trajectory vs running each to budget.
- Late-window certainty stats per captured basin: log-prob, entropy, alt-prob, logit-gap aggregated over the last `stats_window` steps. Ranges across the v0.2 catalog: H from 0.64 to 4.88; gap from 1.00 to 6.64.
- Categorical regularities across starting tokens: whitespace-prefix starts dominate the high-coalescence basins; punctuation starts converge to memorized boilerplate openings (medical-paper, code-header).

Scaling beyond 100 (toward vocab-exhaustive) is filed under Phase 3 in-fill, choosing where to extend on the basis of what the small-scale run surfaced.

## Phase 2 — representative-deep adjudication and basin formalization (closed at small scale)

The representative-deep dip ran on 2026-05-01 (commit `343e2fc`) on 6 selected candidates from the broad-shallow ensemble (ranks 0, 4, 6, 14, 27, 28). All 6 reached `window_cap` at L_arch=2047; all 6 adjudicated as true asymptotic basins under hard-cap T=0 by every signal in design-reqs v2.2 (chosen log-prob → 0, entropy → 0, alt-prob → 0). Selection bias caveat in the entry: 5/6 were chosen because they flagged a token-level cycle, biasing the set toward likely-basin trajectories.

Adjudication, per candidate cycle: does the probability mass on continuation tokens hold or grow with depth, or does it erode? Does the alt-token at cycle steps remain a low-probability stranger, or does it ascend? Does entropy stay collapsed, or does it rise as the model integrates more of the cycle's history? The pattern across these indicators distinguishes true asymptotic attractors from extended transients.

**Basin detection v1 + catalog formalization closed across commits `ae95f32` → `08b0ba5`:**
- Cycle-detection logic in `scripts/representative_deep.py` was promoted to a basin-detection probe in `peirce/basins.py`, per the [records design](design-reqs-records.md) probe interface.
- Basin identity formalized as the cycle token-id tuple (canonical hashable identity) plus cycle text (decoded, human-readable) plus late-window probability profile. Right level of abstraction validated empirically: trajectories from distinct prefixes that converge to the same cycle are recognized as the same basin.
- Basin catalog established as `basins.md`, append-only by entry, currently at v0.2 (19 basins / 28 trajectories under the runtime predicate at commit `08b0ba5`).
- Runtime basin-capture predicate landed in `peirce/basins.py` with a K-rep confirmation threshold (default K=4) and a corrected `repetitions_in_cycle_window` count (was `tail_n // period`; now counts actual consecutive cycle blocks back from the tail). Methodological detail and reconciliation against the v0.1 catalog are in the 2026-05-01 commit-`08b0ba5` observations entry.

The two outputs together — formalized detection and a catalog of basins — are what the project actually needed more than persisted trajectories at this stage. Trajectories remain well-described for inference-time observation; basins are the structural objects whose identity must persist.

## Phase 3 — in-fill (active)

Targeted exploration of regions the first two passes surfaced. Two directions are in flight or imminently so; the others are in the candidate set.

**In flight or imminent:**

- **Selection-bias probe.** Re-run the broad-shallow ensemble with budget extended to L_arch under the runtime basin-capture predicate. Adjudicates the open question: do the 72/100 still-transient trajectories at budget=64 reach basins by L_arch, or remain in transient? Naturally surfaces the v0.1 catalog entries that were not re-confirmed under v0.2 K=4 (basins for trajectories 3, 15, 37, 40, 45 in the v0.1 numbering) and tests whether they materialize as confirmed basins at depth. The runtime predicate makes this cheap: trajectories that capture early stop early; only genuinely transient ones run long.
- **Basin detection v2 (entropy-floor / logit-gap-floor probe).** v1 catches structural cycles only — exact token-id repetition with period ≤ max_period. Local-success traps that don't repeat exactly (ascending sequences, ordinal cascades, slowly drifting boilerplate) are invisible to v1 but should show as low-entropy or high-gap floors over windows. Calibration distribution comes from the v1 catalog: every v1 basin's late-window entropy and gap profile is a confirmed positive; threshold tuning targets specificity to those without false-positive on natural transients. Naturally complementary to the selection-bias probe — v2 detection running on the extended trajectories likely catches additional basins missed by v1.

**Candidate, not yet scheduled:**

- Higher k from `[BOS]` — extending toward vocab-exhaustive — to test whether categorical regularities seen in the top-100 hold in the OOD tail and to populate the basin catalog with more specimens.
- Alternate initial conditions on bounded subsets — multi-BOS prefixes, short seeded prompts — to begin convention-sensitivity characterization.
- Plumbing-sensitivity probes — minor variations in tokenizer normalization, special-token handling — to tag findings as plumbing-stable or plumbing-sensitive.
- Specific deeper dives into trajectories whose adjudication was ambiguous: probability-gap dynamics at finer resolution, comparison to neighboring trajectories in start-token space.

In-fill is cheap relative to broad-shallow and representative-deep, because each in-fill probe is small. The point of Phase 3 is that the first cycle does not stop at adjudication; it pushes into specific regions until the cycle's primitives — terminal-event distribution, candidate-basin signatures, escape patterns, plumbing dependencies — are stable enough that re-founding moves or next-cycle moves can be considered on their merits.

## Looking beyond the first cycle

Each axis named in *the shape of inquiry* opens a later cycle. Some forward-looking threads have their own design surfaces; others are parked in [ideas.md](ideas.md) until they earn one.

**With existing design surfaces.**

- **Targeted basin steering.** Minimum-token interventions on identified context-foundations to test reachability of hypothesized basins. Specified in [design-reqs-steering.md](design-reqs-steering.md). Prerequisites named there; Phase 2's basin formalization is one of them.

**Parked in ideas.md.**

- **Transients as the territory of useful generation, EOS as success state, external fitness probes.** Reframe of basins as failure-modes-for-engineering vs phenomena-for-science; would graduate to its own design surface once productive-vs-degenerate-transient classification becomes formalizable and external fitness probes have been exercised.

**Deferred without formal design surface yet.**

- **T>0 perturbation cycle.** With the deterministic substrate mapped, temperature becomes the first natively continuous perturbation. Small T probes the immediate neighborhood of T=0 attractors; rising T traces the transition from substrate-like behavior to typical-sample-like behavior. The kernel formulation accommodates this without architectural change.
- **Sliding-window inference cycles.** Naive sliding (BOS decays out of context), stabilized sliding (attention sinks pin first-k tokens), chunked sliding with grain. Each studies a distinct post-L regime; each is its own cycle with its own broad-shallow → representative-deep → in-fill instantiation.
- **Discrete perturbations beyond steering.** Token injection at scale, context manipulation, structured prompt frames. The project's eventual core, currently deferred.
- **Cross-model.** Running the same first cycle on a second and third model. Cross-model basin identity becomes the first place richer fingerprinting earns its keep, and likely the first place the project's distinctive contribution becomes visible against existing work.
- **Trajectory persistence.** Records held in-memory and observation entries are sufficient for inference-time investigation. Full persistence (artifact format, indexing, cross-run query surface) becomes the right move when `peirce/records.py` is sufficiently stable to commit to the schema, *or* when persistence is blocking something critical (cross-run basin coalescence at scale, contributor-shareable artifacts, the cross-model cycle).
- **Dense N-gram caching.** Frequent context prefixes admit dense kernel storage as an engineering optimization on the trajectory engine's working set. Filed for much later; coherent with the trajectory framing without driving current decisions.

## Prior art worth tracking

These are the references most directly aligned with the project's framing as it currently stands. They are not the only relevant work; they are the work most likely to either anticipate or sharpen what the project finds.

**Zekri et al. 2024, "Large Language Models as Markov Chains" (arXiv 2410.02724).** Formalizes language models as sparse stochastic kernels over vocabulary with block structure determined by context. Provides theoretical results on stationary distributions, mixing, and convergence. Relevant as both reference and reality check — where the theory predicts a phenomenon, the empirical work either confirms or sharpens; where the empirical work surfaces phenomena the theory cannot describe, that is the project's distinctive territory.

**Holtzman et al. 2019, "The Curious Case of Neural Text Degeneration."** Establishes that low-temperature generation enters repetitive attractors and motivates nucleus sampling. The first-cycle observations live in exactly the regime that paper named as a problem; the project asks instead what those attractors are and whether they have structure worth taxonomizing.

---

*This brief assumes familiarity with the [Foundations](foundation.md), [Design Requirements](design-reqs.md), and the records and steering companion docs, and uses their vocabulary without re-introduction. Empirical findings are in [observations.md](observations.md); forward-looking threads not yet ready for design surfaces are in [ideas.md](ideas.md).*
