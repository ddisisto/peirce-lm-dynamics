# Peirce — Project Brief

*Companion to the Foundations and Design Requirements documents. Maps the initial arc of work — through the L=1 proof of concept and slightly beyond — and captures the architectural decisions reached in design discussion.*

*Status: v0.1. The brief is more revisable than the requirements and far more revisable than the foundations. It is expected to evolve as the L=1 work uncovers what was true and what was not. Substantial revision is recorded; minor edits are not.*

---

## What this document is

The Foundations document specifies what the project studies and the frame it studies through. The Design Requirements document specifies what the project must do and the structural properties it must have. Neither commits to a specific first move. This document does.

It maps the initial arc and captures the architectural decisions made in the discussions leading to it. Where decisions remain open, they are named. Where decisions have been made, the reasoning is preserved alongside them so they can be revisited deliberately rather than overturned by drift.

This document is downstream of the Foundations and Requirements; nothing here overrides anything there.

## The shape of the arc

The first cycle's work has a shape, not just a list. Five phases, each producing artifacts that the next phase depends on. Phases are not strict; they overlap; what matters is the dependency structure.

**Phase 0 — Substrate selection and harness.** Choose the model and inference setup the L=1 sweep will run on. Document the convention. Get the harness producing trustworthy logits at all. Pin the open decisions named below.

**Phase 1 — L=1 exhaustive sweep.** Produce the dense L=1 specimen: for every token in the vocabulary, the next-token distribution conditioned on that single-token context. Store it. Analyze its structure — cycles, fixed points, basins, connected components, predecessor and successor statistics. The artifact is a first-class project citizen and the substrate against which all later work is interpreted.

**Phase 2 — Trajectory engine.** Build the generator that produces trajectories at any L, recording per-step thin metadata. Validate it against the L=1 dense specimen by closed-form check. Implement the predicate framework that will accumulate stop conditions, basin detectors, and event observers over time.

**Phase 3 — L>1 trajectories on the L=1 substrate.** Run trajectories at growing context lengths. Use the L=1 graph as the baseline for interpretation: what the model does at L=k that it does not do at L=1 is the first place to look for non-substrate phenomena.

**Phase 4 — First taxonomic moves.** Identify candidate phenomena that warrant naming. Distinguish substrate-derived from emergent. Decide what the next cycle's questions are. Re-found if necessary.

The crystal hypothesis is not directly tested in this arc. L=1 cannot test it; L>1 trajectories on the L=1 substrate produce the *baseline* against which any future crystal claim would be measured. Earning the right to make a crystal claim is itself part of the work.

## Architectural decisions

These are the decisions that have been made and the reasons they were made. They are revisable but not in passing — undoing them requires the same kind of explicit consideration that made them.

**The Markov kernel is the substrate object.** At L=1 the project studies a stochastic transition kernel over the vocabulary — the row-stochastic matrix whose entry K[i,j] is the model's probability of token j given context [i]. The argmax graph at T=0 is one analytic view of this kernel; threshold graphs, top-k graphs, stationary distributions, mixing times, spectral gap, and communicating classes are others. The kernel generalizes them and connects directly to standard dynamical-systems machinery without bespoke vocabulary.

**Two artifact types.** The L=1 sweep produces a dense kernel artifact: vocab × vocab, fp16, stored in chunked Zarr with a manifest sidecar specifying model identifier, model version, inference configuration, and code commit. Trajectory runs produce thin records: per-step scalars including chosen token, log-probability of that token, distribution entropy, and (provisionally) the second-most-likely token and its probability. Five scalars per step; tabular storage (Parquet or equivalent).

**The dense artifact is the engine's validation specimen.** The trajectory engine, run at L=1, must produce thin records whose values are exact functions of the corresponding rows of the dense artifact. This is a closed-form check, not a statistical one. Passing it certifies that the engine reads the model correctly; failing it indicates a bug, not a discrepancy. The dual role of the L=1 artifact — phase-space data and engine validation specimen — is intentional and should not be refactored away as redundancy.

**Fingerprinting interfaces are designed; implementations earn their keep.** Basins are stored structurally, not pre-fingerprinted. A fingerprint is a function from a structurally-stored basin to a stable identifier; the interface is small. The first implementation is the simplest one Phase 1 requires (likely the cycle expressed as a sorted set of token strings, or a normalized rotation of the cycle itself). More elaborate fingerprints — embedding-distance, dim-reduced, structural-similarity — wait for questions that require them. The cross-model identity question is the natural place for richer fingerprints to earn their keep, and it does not appear until Phase 4 at earliest.

**Trajectory generation is predicate-based.** A trajectory generator yields tokens and consults a list of predicates over (history, position, model state, basin state). Stop conditions, basin-capture detectors, escape detectors, and any future event observers are instances of the same primitive. The set of predicates is open; adding one is registering it. This makes "events we may later define" a non-feature, because the architecture supports them by virtue of the predicate interface.

**EOS is observable, not privileged.** The trajectory engine supports an indefinite mode in which EOS is not a terminator but an event observable in the trajectory — counted, located, related to surrounding context like any other token. This is a first-class mode, not a debug feature. The meaning of EOS is its role in the dynamics, not a status imposed on the dynamics.

**Inference convention is pragmatic and instrumented.** The first sweep uses the most null-like context convention the chosen model supports — typically just the BOS token followed by the single-token context, fed to the inference engine directly. Chat-template wrappers and elaborate framing are not required at this stage and are not ruled out for later. The sensitivity of L=1 results to inference plumbing is itself a finding to be characterized, not a problem to be eliminated upfront.

## Open decisions

These remain to be pinned during Phase 0.

**Model choice.** Candidates include Pythia (mature interpretability ecosystem, fully open training data, deterministic-replay infrastructure) and small Llama or Qwen variants (more relevant to current frontier dynamics). The choice trades off instrumentation maturity against contemporary relevance. Either is workable; the decision should be made deliberately rather than by drift, and revisited when the second model is chosen for cross-model work.

**The exact thin-record schema.** Five scalars per step is the proposed shape; the specific fields named above are defensible defaults but not load-bearing. Adjustments are cheap before any trajectories are stored and expensive after. Pin before Phase 2 produces persistent records.

**The canonical fingerprint for Phase 1.** The simplest reasonable choices have different properties: a sorted set of token strings (rotation-invariant, content-only), the cycle in canonical rotation order (preserves sequence), a hash of the cycle's logit signature (model-specific but precise). The decision is small but should be made on purpose.

**Storage layout details.** Zarr chunking strategy, manifest schema, trajectory-record sharding. These are mechanical decisions that nonetheless determine how easily artifacts can be referenced, deduplicated, and re-derived.

## What follows L=1, named and deferred

The Design Requirements name several directions deferred from this cycle. The brief preserves the same deferrals and adds shape to what comes after L=1 if Phase 4 produces stable primitives.

**Perturbation studies.** Once the L=1 substrate is mapped and the trajectory engine is trustworthy, perturbations become studyable as operators that move trajectories between basins. Temperature is the natively continuous knob, which the kernel formulation accommodates without architectural change; token-injection and context-manipulation perturbations follow as discrete operators on top.

**Cross-model comparison.** Running the same L=1 sweep on a second and third model produces directly comparable kernel artifacts. The cross-model identity question — when is a basin in model A "the same" as a basin in model B — is the first place richer fingerprinting earns its keep, and likely the first place the project's distinctive contribution becomes visible against existing work.

**Higher-L dynamics.** Phenomena that live above the L=1 substrate but below long-context behavior. Crystals, if they are real, plausibly first appear in this regime.

**Long-context dynamics.** Trajectories at L approaching or exceeding the model's training context. A different empirical regime; the apparatus built for shorter L should generalize but the phenomena likely will not.

**Dense N-gram caching as adaptive compression.** Frequent context prefixes admit dense kernel storage analogous to the L=1 artifact — caching the next-token distribution for common N-grams while uncommon contexts fall back to live model evaluation. The shape is engineering (compression of the trajectory engine's working set) but coherent with the kernel-as-substrate framing: a dense N-gram table is the kernel restricted to a specific frequent context, and nothing architectural has to change to accommodate it later. Connects to the block structure described in Zekri et al. as the empirical shadow of a theoretical observation. Filed for much later; not driving current decisions.

## Prior art worth tracking

These are not the only relevant references; they are the two most directly aligned with the project's framing as it currently stands.

**Zekri et al. 2024, "Large Language Models as Markov Chains" (arXiv 2410.02724).** Formalizes language models as sparse stochastic kernels over vocabulary with block structure determined by context. Provides theoretical results on stationary distributions, mixing, and convergence. Does not release artifacts. Relevant as both reference and reality check — where the theory predicts a phenomenon, our empirical work either confirms or sharpens; where the empirical work surfaces phenomena the theory cannot describe, that is the project's distinctive territory.

**Holtzman et al. 2019, "The Curious Case of Neural Text Degeneration."** The canonical reference for repetition collapse and the rationale for nucleus sampling. Establishes that low-temperature generation enters repetitive attractors; the project's L=1 sweep formalizes the substrate from which that observation follows.

---

*This brief assumes familiarity with the Foundations and Design Requirements documents and uses their vocabulary without re-introduction. It will be revised as Phase 0 closes and again as each subsequent phase produces material the brief should reflect.*
