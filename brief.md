# Peirce — Project Brief

*Companion to the [Foundations](foundation.md) and [Design Requirements](design-reqs.md). Maps the shape of inquiry across cycles, and the first cycle's concrete moves.*

*Status: v0.2. The brief is more revisable than the requirements and far more revisable than the foundations. Substantial revision is recorded; minor edits are not.*

---

## What this document is

The Foundations specify what the project studies and the frame it studies through. The Design Requirements specify what the system must do and the structural properties it must have. Neither commits to a specific first move. This document does.

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
- **Per-step thin records.** Token (id and decoded), log-prob of chosen, distribution entropy, second-most-likely token + its probability. Five fields per step. Tabular storage (Parquet) with manifest sidecar.
- **Candidate-basin recognition.** Manual plus ad-hoc cycle-finding for the first cycle. No formal detector is built; we do not yet know what signature it should match. Trajectories containing structural cycles within budget are flagged; whether each flag is a true asymptotic attractor or an extended transient is the question the representative-deep pass adjudicates by watching the probability dynamics.

The smoke test's `'\n' → '\n'` self-loop at step 1 is not assumed to be a true fixed point. Whether the leading-whitespace regime escapes into content — titles, banners, metadata blocks reflected from the training distribution — is among the things the first cycle is set up to find out.

## Phase 0 — substrate and harness

Phase 0 closes a small set of decisions and stands up the infrastructure the rest of the cycle depends on.

**Pinned.**
- Model: pythia-1b-deduped, fp32, CUDA on GTX 1070.
- Tooling: uv with Python 3.12, dependencies via `uv add`.
- Repo layout: flat package at `peirce/` with `__main__.py` entry, scripts in `scripts/`, data artifacts under `data/` (gitignored).
- Inference convention: direct token feed (`[BOS, ...]`) with no chat-template wrapper. Sensitivity to plumbing is a finding to characterize, not a problem to eliminate upfront.

**To pin during Phase 0.**
- Module structure: an `engine` providing trajectory generation given a model, initial condition, predicate set, and run config; a `predicates` module providing the open set of stop conditions and event observers; a `manifest` module providing run-config + provenance serialization.
- Trajectory record schema: the five fields above, in Parquet, one row per step, partitioned by trajectory id. Manifest sidecar in JSON or YAML capturing model id and revision, code commit, k, budget, inference strategy, initial condition, sampling config (T=0).
- Predicate framework: a small uniform interface over (history, position, model state, run state) → terminal-event tag or None. EOS-detection, structural-cycle detection, budget-cap, and window-cap are all instances of this primitive. Adding a new event observer is registering a new predicate.
- Smoke-test rework: replace `scripts/smoke_l1.py` with a smoke for the trajectory engine that produces a small ensemble and reads it back.

**Deliberately deferred.**
- Basin fingerprinting. The signature that distinguishes a true attractor from an extended transient at the level of intensive features is itself an empirical question; a formal fingerprint earns its keep once there are specimens to know what it should match. First-cycle annotation is structural-cycle detection plus a probability-dynamics summary, both post-hoc.
- Dense kernel artifacts. The full vocab × vocab transition kernel at any specific context is computable on demand; storing one is not load-bearing for the first cycle. The single-step view at `[BOS]` is implicitly captured by step 0 of the trajectory ensemble.
- Engine validation against a separately produced dense reference. Closed-form spot-checks against direct logit calls suffice; a dense-artifact phase is not warranted at first-cycle scale.

## Phase 1 — broad-shallow ensemble

Run the 100 × 64 ensemble. Store thin records and manifest. Inspect by hand.

Primary observables:

- Distribution of terminal events: how many EOS-terminate within 64 steps, how many trigger candidate-basin flags, how many budget-cap as still-running transients.
- Entropy traces around candidate-cycle entry: does entropy collapse and stay collapsed (capture-like) or does it drop and recover (extended-transient-like).
- Top-1 / top-2 gap dynamics in candidate-cycle regions: does the gap widen with depth (capture-like) or narrow (escape pressure rising).
- Categorical regularities across starting tokens: do tokens of similar surface kind (whitespace, punctuation, function words, content words) produce similar trajectories, or does trajectory behavior cut across surface categories.

Output: a trajectory ensemble citable as a first-class artifact, a notebook or memo summarizing what was actually observed, and a list of candidate basins selected for the representative-deep pass.

## Phase 2 — representative-deep adjudication

Select candidates from Phase 1. Extend toward L_arch. Watch probability dynamics over the extended depth.

Adjudication, per candidate cycle: does the probability mass on continuation tokens hold or grow with depth, or does it erode? Does the second-most-likely token at cycle steps remain a low-probability stranger, or does it ascend? Does entropy stay collapsed, or does it rise as the model integrates more of the cycle's history? The pattern across these indicators distinguishes true asymptotic attractors from extended transients.

Output: a typology in two cuts — candidate-basins that survived adjudication (provisional true attractors) and candidate-basins that escaped (extended transients, with the depth and signature of escape recorded). Both are findings.

## Phase 3 — in-fill

Targeted exploration of regions the first two passes surfaced. Plausible directions, chosen by what Phase 2 actually found:

- Higher k from `[BOS]` to test whether categorical regularities seen in the top-100 hold in the OOD tail.
- Alternate initial conditions on bounded subsets — multi-BOS prefixes, short seeded prompts — to begin convention-sensitivity characterization.
- Plumbing-sensitivity probes — minor variations in tokenizer normalization, special-token handling — to tag findings as plumbing-stable or plumbing-sensitive.
- Specific deeper dives into trajectories whose adjudication was ambiguous: probability-gap dynamics at finer resolution, comparison to neighboring trajectories in start-token space.

In-fill is cheap relative to broad-shallow and representative-deep, because each in-fill probe is small. The point of naming Phase 3 is to mark that the first cycle does not stop at adjudication; it pushes into specific regions until the cycle's primitives — terminal-event distribution, candidate-basin signatures, escape patterns, plumbing dependencies — are stable enough that re-founding moves or next-cycle moves can be considered on their merits.

## Looking beyond the first cycle

Each axis named in *the shape of inquiry* opens a later cycle.

- **T>0 perturbation cycle.** With the deterministic substrate mapped, temperature becomes the first natively continuous perturbation. Small T probes the immediate neighborhood of T=0 attractors; rising T traces the transition from substrate-like behavior to typical-sample-like behavior. The kernel formulation accommodates this without architectural change.
- **Sliding-window inference cycles.** Naive sliding (BOS decays out of context), stabilized sliding (attention sinks pin first-k tokens), chunked sliding with grain. Each studies a distinct post-L regime; each is its own cycle with its own broad-shallow → representative-deep → in-fill instantiation.
- **Discrete perturbations.** Token injection, context manipulation, structured prompt frames. Operators that move trajectories between basins; the project's eventual core, currently deferred until the unperturbed substrate exists to interpret perturbations against.
- **Cross-model.** Running the same first cycle on a second and third model. Cross-model basin identity becomes the first place richer fingerprinting earns its keep, and likely the first place the project's distinctive contribution becomes visible against existing work.
- **Dense N-gram caching.** Frequent context prefixes admit dense kernel storage as an engineering optimization on the trajectory engine's working set. Filed for much later; coherent with the trajectory framing without driving current decisions.

## Prior art worth tracking

These are the references most directly aligned with the project's framing as it currently stands. They are not the only relevant work; they are the work most likely to either anticipate or sharpen what the project finds.

**Zekri et al. 2024, "Large Language Models as Markov Chains" (arXiv 2410.02724).** Formalizes language models as sparse stochastic kernels over vocabulary with block structure determined by context. Provides theoretical results on stationary distributions, mixing, and convergence. Relevant as both reference and reality check — where the theory predicts a phenomenon, the empirical work either confirms or sharpens; where the empirical work surfaces phenomena the theory cannot describe, that is the project's distinctive territory.

**Holtzman et al. 2019, "The Curious Case of Neural Text Degeneration."** Establishes that low-temperature generation enters repetitive attractors and motivates nucleus sampling. The first-cycle observations live in exactly the regime that paper named as a problem; the project asks instead what those attractors are and whether they have structure worth taxonomizing.

---

*This brief assumes familiarity with the [Foundations](foundation.md) and [Design Requirements](design-reqs.md) and uses their vocabulary without re-introduction.*
