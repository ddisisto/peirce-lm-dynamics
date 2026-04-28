# Peirce — Design Requirements

*Companion to the Foundations document. Specifies what the project must do, what properties it must have, and what it deliberately does not commit to. Implementation details belong downstream.*

*Status: v0.1. Requirements are revisable; revisions are recorded. Significant revisions that conflict with the Foundations require a re-founding cycle.*

---

## Immediate scope

The first cycle of work targets the simplest tractable case: minimal context, single-token transitions, exhaustive sweep.

**Vocabulary sweep at L=1.** For a given model and inference configuration, enumerate the next-token distribution conditioned on each single-token context across the full vocabulary. At temperature 0, this yields a deterministic mapping from each token to its argmax successor: a directed graph over the vocabulary that constitutes the L=1 phase space.

**Structural analysis of the L=1 graph.** Identify fixed points (tokens mapping to themselves), cycles, basins of attraction in the graph-theoretic sense, source tokens (no predecessors), sink tokens (many predecessors), and the connected components. The graph itself is a first-class artifact; its structural properties are the first taxonomic targets.

**Recursion into short trajectories.** For initial conditions that do not immediately enter a known fixed point or cycle, follow the trajectory forward at minimal context until it enters an attractor or exceeds a defined transient budget. Record the transient and the attractor entered.

**Initial basin identification.** Define what constitutes a basin operationally — initially via the graph-theoretic notion at L=1, with a clear path toward extension at higher L. Distinct basins should be distinguishable; trajectories should be assignable to basins; the act of "encountering the same basin again" should be a meaningful operation, not a guess.

**Sensitivity to inference plumbing.** Document and test the dependence of L=1 results on inference setup details: BOS handling, default system tokens, position encoding behavior at minimal positions, sampling implementation. Findings that prove sensitive to plumbing are tagged as such; findings stable across plumbing variations are stronger.

The immediate scope does not extend to longer contexts, cross-model comparison, perturbation studies, escape characterization, or higher-order dynamics. Those become possible once the L=1 phase space is mapped and the primitives that describe it are stable.

## Structural commitments

These are properties the system must have regardless of the specific work being done with it. They protect the project's ability to grow without committing to any particular direction of growth.

**Basins have stable identities.** A basin discovered in one run, on one model, under specific conditions must be recognizable when encountered again — by the same observer, by another observer, on the same model under different conditions, or on a different model. The mechanism by which identity is established (fingerprinting, canonical representation, structural signature) is an implementation question; that identity is preserved is a requirement. The fingerprint must be defined in terms of observable properties of the basin, not accidents of how or when it was first found.

**Findings are reproducible.** Any reported finding — an identified basin, an observed transition, a classification — must be re-derivable from recorded conditions: model identifier and version, parameters, inference configuration, code version, sampling seed where relevant. Findings without sufficient provenance to be re-derived are not findings; they are anecdotes, and are recorded as such if recorded at all.

**Findings are addressable.** Every persistent object the project produces — a basin, a trajectory, a classification, a fingerprint — has a stable identifier by which it can be referenced. References between objects are first-class. The project's accumulated knowledge is a graph, not a pile of files; the data model reflects this.

**Model-agnosticism where possible.** The framework's primitives — trajectory, basin, transient, perturbation, escape, fingerprint — must not assume a specific model architecture, size, tokenizer, or training distribution. Specific findings will be model-specific; the apparatus for finding them must not be. Where model-specific assumptions are unavoidable, they are marked as such and isolated from the model-agnostic core.

**Contributions are first-class.** A finding produced by one person, on one machine, in one session, should be expressible in a form that another person, on another machine, in another session, can read, verify, build on, and reference. This is a constraint on data formats, on identifiers, and on the system's notion of provenance. It does not require any specific collaboration mechanism; it requires that collaboration not be precluded by architectural decisions made now.

**The L=1 graph is a citizen.** The directed graph over vocabulary produced by the L=1 sweep is a primary specimen of the project, not a temporary scaffolding. It is stored, versioned, addressable, and referenced by higher-L analyses. Higher-L work is interpreted against the L=1 substrate, not in isolation from it.

**Foundations supremacy.** No implementation decision overrides the Foundations document without a deliberate re-founding cycle. Conflicts between an implementation choice and the Foundations are resolved by either revising the implementation or initiating a re-founding — never by silently allowing the implementation to drift.

## Out of scope (named, deferred)

These are possibilities worth preserving as legitimate future directions but explicitly not driving current decisions. Naming them here protects the immediate work from their gravitational pull while preserving them as candidates for later cycles.

**Crowdsourced data collection and contribution.** A future cycle may treat the project as infrastructure for distributed exploration of model dynamics, with contributors running sweeps, submitting findings, and building on each other's work. Current architecture must not preclude this (see structural commitments) but does not implement it.

**Gamification and public-facing UX.** Examples discussed include: longest-stable-basin challenges, curated quasi-periodic discoveries with naming rights, model-specific exploration leaderboards. These are deferred as concrete features; the architectural property they share — that findings are first-class, attributable, and shareable — is preserved as a structural commitment.

**Cross-model comparative taxonomy at scale.** Comparing basin structure across many models is high-value but premature. The L=1 work on a single model will produce the primitives that such comparison would require; until those primitives are stable, comparison would be measuring with an unfinished ruler.

**Perturbation and escape studies.** The dynamics under temperature, token injection, and context manipulation are central to what the project is ultimately about. They are deferred until the unperturbed L=1 phase space is mapped, because we want a stable substrate to interpret perturbations against.

**Higher-order dynamics.** Long-window behavior, hierarchical attractor structure, cycles within cycles, slow drift between basins. All deferred. All architecturally protected.

**Theoretical claims about consciousness, agency, or "what the model is doing" in interpretive senses.** The project's empirical work may eventually inform such questions, but the questions are not within scope and project documents do not stake claims on them. The Foundations note the philosophical lineage; the requirements forbid the project from being captured by it.

## Architectural non-negotiables

The smallest set of constraints whose violation would compromise the project's ability to do its work or to grow.

**Reproducibility above convenience.** Where a choice between a more reproducible and a more convenient implementation arises, reproducibility wins. This includes accepting friction in the development process to ensure findings can be re-derived.

**Provenance is structural.** Every persistent object carries the metadata required to re-derive it. This is not a logging concern, not a documentation concern, and not deferrable to "later when we clean things up." It is part of the object's identity from the moment it is created.

**Vocabulary is load-bearing.** Terms defined in the Foundations have specific operational meaning within the project. Code, documents, and discussions use these terms with that meaning. When usage drifts — when "basin" starts meaning something subtly different in one corner of the project than in another — this is a signal of either conceptual movement (worth surfacing) or decay (worth correcting). Either way it is not ignored.

**Failure to fit existing literatures is acceptable.** The project will produce observations and categories that may or may not align with existing terminology in dynamical systems theory, machine learning interpretability, computational linguistics, or philosophy of mind. Where alignment is natural, it is noted. Where it is forced, it is resisted. The project's job is to describe what it finds accurately, not to translate findings prematurely into the vocabulary of fields that may have framed the questions differently.

## Signals for re-founding

The Foundations are frozen by default; the requirements derived from them are revisable but stable. Certain signals warrant deliberate reopening of either or both. They are recorded here so that re-founding is recognized when it is appropriate, rather than felt as an emergency.

A signal for revising the requirements: a finding from the immediate work that requires extending or modifying the structural commitments. Example — discovering that basin identity at L=1 cannot be defined in a way that extends to higher L. The requirement adapts; the foundations may not need to.

A signal for re-founding: a finding that contradicts a working hypothesis in the Foundations, or that introduces a phenomenon the Foundations' vocabulary cannot describe without strain. Example — observing dynamics that are clearly not characterizable as crystallization, replication-with-error, or any combination thereof. The Foundations are reopened; the requirements may need to follow.

A signal for re-founding the project as a whole: accumulating drift between the active understanding and the documents, such that working on the project feels meaningfully disconnected from what the documents describe. The drift itself is the signal; its specific content is what the re-founding cycle examines.

The point of naming these signals is not to make re-founding frequent. It is to make re-founding a known, available move, so that when one is needed it is recognized rather than resisted.

---

*This document is downstream of the Foundations and assumes familiarity with the vocabulary and frame defined there. It does not reproduce that content; it specifies what the project must do given that frame, and what it deliberately does not yet do.*