# Peirce — Steered Trajectories: Design Requirements

*Companion to the primary [Design Requirements](design-reqs.md) and the [Records Design](design-reqs-records.md). Specifies the design and methodological frame for a research thread the project will pursue once first-cycle prerequisites are met: targeted basin steering through minimum-token interventions on identified context-foundations.*

*Status: v0.1, forward-looking. The thread itself is deferred in the primary design requirements (see "Perturbation and escape studies"); this document specifies it well enough that picking it up later does not lose context.*

---

## What this document is

The primary design requirements specify what the project is doing now. The records design specifies what gets recorded when it does it. This document specifies a *future* research thread — one that has emerged from the first-cycle work clearly enough to warrant its own design surface, but whose prerequisites are not yet met.

Capturing it now serves two purposes. First, the reasoning that produced the thread is fresh and worth preserving with the thread itself, not reconstructed later. Second, naming the thread shapes what counts as readiness — the prerequisites become explicit milestones against which "is the project ready for this yet?" can be answered.

This document is downstream of the Foundations and assumes familiarity with both companion design documents.

## The shape of the inquiry

The thread proposes a specific kind of experiment over the model's dynamics:

1. **Identify context-foundations.** Short token-prefix structures (often a single token or a few) that reliably push trajectories into a particular *kind* of basin under hard-cap T=0 — Python code, markdown table fences, wiki-style boilerplate, code-comment Chinese, contributor-list openings, and so on. Several have already surfaced in first-cycle broad-shallow work.

2. **Characterize the transient.** For each context-foundation, identify where during the leading transient (before basin entry) the model's decision surface is most leverageable — typically the steps with lowest rank-1/rank-2 logit gap, highest entropy, or highest alt-token probability. These are the candidate intervention sites.

3. **Hypothesize a target basin.** Name in advance a basin the experimenter conjectures is reachable from the chosen context-foundation — for example, "Python list comprehension over a list of strings," "wiki article header about a 19th-century scientist," "iambic-pentameter quatrain about weather."

4. **Intervene minimally.** Inject the smallest set of tokens, at the leverage-points identified in (2), that would plausibly steer the trajectory toward the target. Generate from the modified context under hard-cap T=0.

5. **Adjudicate reachability.** Did the trajectory enter the target basin? Under what intervention budget? With what intervention positions? Successful steering with N tokens of intervention is a *reachability claim*: the target basin is reachable from this context-foundation with intervention cost ≤ N.

The object of study shifts. Rather than "what basin does this trajectory fall into?" — descriptive — the question becomes "can this trajectory be landed in that basin?" — predictive, abductive, falsifiable. The text the model produces during a successful run is incidental; the citable finding is the reachability claim and the intervention specification that produced it.

## Why this thread

Two motivations, both grounded in earlier work.

### As a natural extension

First-cycle broad-shallow runs already surfaced reliable context-foundations. Whitespace prefixes route to table-fence basins; punctuation prefixes route to memorized boilerplate; the `_` prefix routes to a phrase-cycle basin around "first thing to note." These are reproducible facts about the model's geometry. The next move from "this prefix tends to enter basin B" is "with what minimum intervention can it enter basin B′ instead?" That is a natural cartographic densification of regions the broad-shallow sweep has already located.

This thread also exercises the *crystal hypothesis* in active form. If a basin's stability derives from relational density of its content rather than from sampling-dynamical accident, then crystals should be reachable from many context-foundations with relatively small interventions, while non-crystal basins should require either matching context-foundations or larger interventions. A characterized reachability geometry is exactly the kind of evidence that distinguishes crystal basins from contingent ones.

### As loop-closure with the observer's role

The first-cycle methodology directs attention toward low-certainty regions — the model's decision surfaces — as the places where per-token reading is most informative. This is structurally good against the failure mode where a substrate trained on humanity's compressed attentional history becomes a personal mirror for an individual observer. But it does not by itself answer the question of what the project produces beyond increasingly fine characterization of one model's decision surfaces under one observer's attentional choices.

Steering experiments answer that. They produce *predictive* findings about the substrate's geometry — claims that other observers can test by re-running with the same model and stack, and claims about the model that hold independent of which observer chose to investigate them. The hypothesized basin is named in advance; the success criterion is reachability, not aesthetic resonance with the produced text. This shifts the work from "characterize what the substrate produces in my direction" to "test whether the substrate's geometry has the structure I conjecture." The text becomes a specimen on a slide rather than something to read for meaning.

This is abduction in active form. The hypothesis is a structural claim about the dynamics; the test is an attempted demonstration; the outcome is informative whether positive or negative.

## Working vocabulary

Names are provisional and may evolve.

- **Context-foundation.** A short token-prefix structure that reliably routes hard-cap T=0 trajectories into a particular class of basin. Single-token foundations are the simplest case; multi-token foundations may exhibit richer routing. The first-cycle broad-shallow ensemble is the initial catalog.
- **Transient.** The portion of a trajectory before basin entry. As in foundations vocabulary; here the focus is on transient *length*, *intervention sensitivity*, and *commitment profile* (how strongly each step constrains the eventual basin).
- **Intervention.** A modification to the context during generation: a token replacement, an injection, a deletion. Intervention specifications include positions, tokens, and (eventually) intervention type.
- **Target basin.** A basin hypothesized in advance, characterized by the experimenter as the conjectured reachability target. Specification of "what counts as having reached B" depends on basin identity formalization (see prerequisites).
- **Reachability claim.** A finding of the form: "from context-foundation C, target basin B is reachable under intervention specification I, on stack S, at attempt cost N." The citable unit of this thread.
- **Intervention budget.** The size of the intervention specification — typically token count, possibly weighted by intervention type. The minimum-budget reachability is the thread's primary scaling axis.
- **Intervention sensitivity.** A property of a context-foundation's transient: where during the transient interventions have leverage. Quantifiable via existing per-step certainty signals (logit gap, entropy, alt-prob).
- **Basin coordinate.** A pair `(context-foundation, intervention-specification)` that lands the trajectory in a named basin. The proposal: basins acquire coordinate sets, and the relationships among coordinates that reach the same basin become a structural property of the basin itself.

## Prerequisites

This thread cannot run cleanly until the following are in place. Each is an explicit milestone for "is the project ready?"

### Basin identity is formalized

"Hit basin B" requires knowing when two trajectories are in the same basin. The first-cycle work has adjudicated specific candidates as true asymptotic basins under a single observer's judgment, but has not formalized basin coalescence — when do two distinct trajectories' tail content count as instances of the same basin? Until basin identity has a fingerprint or canonical representation, "reached B" reduces to "produced text that looks like B-trajectory output to me," which collapses the predictive structure of this thread back into descriptive aesthetics.

The structural commitment in the primary design requirements ("Basins have stable identities") names this requirement; the present thread depends on its operationalization.

### Context-foundation catalog exists at scale

The first-cycle broad-shallow ensemble is the initial seed. A useful catalog characterizes for each foundation: the trajectories it produces under hard-cap T=0; the basin or basins those trajectories enter; the transient length distribution; the intervention-sensitivity profile across the transient. Building this catalog is partly already done (every broad-shallow trajectory contributes a row); explicit cataloging with derived per-foundation summaries is a separate step.

### Intervention probe machinery

The records design specifies probes as `(window, records) → result` — analytic, operating on existing trajectories. This thread requires a different probe shape: `(context-foundation, intervention-specification, target-basin) → outcome`, which includes generation. The architecture must accommodate intervention probes as a distinct probe class, with their own provenance requirements (the intervention specification is part of any resulting trajectory's identity).

### Inference machinery for context modification

The trajectory engine generates from a fixed prefix. Steered trajectories require generation under interventions: token replacement at specified positions, injection at specified positions, generation continuing from a modified context. This is implementable on the existing engine but is not yet implemented.

## Methodological commitments

Specific to this thread, distinct from the more general project commitments. Capturing them here so the discipline that makes this thread non-mirror-amplification is explicit and durable.

### Hypothesized basins are named in advance

The target basin is specified before the experiment runs. Post-hoc claims of the form "this trajectory looks like basin B, so we reached B" do not count as reachability findings. The criterion for reaching B is part of the experiment design, not part of the experiment's interpretation.

### Minimum-intervention discipline

The success metric is reachability under *minimum* intervention budget. Reaching a target basin with a 100-token prompt that paraphrases the target is not informative about the substrate's geometry; reaching the same basin with a 3-token intervention at a specific position is. The thread cares about the minimum, not just any successful path.

### Negative results are findings

Failure to reach a hypothesized basin from a chosen context-foundation under any practical intervention budget is a finding about the substrate, not a methodological failure. The reachability geometry is informative both at the points where basins are reachable and at the points where they are not.

### Reachability findings are stack-scoped

A reachability claim is scoped to its stack: model + revision + dtype + device + deterministic flags + library versions. Cross-stack generalization of reachability claims is itself an empirical question, not a default assumption. The records design framework handles this; this thread inherits it.

### The text is incidental

What the model produces during a steered run is a specimen, not content. Findings cite the reachability claim and the intervention specification, not the produced text. Decoded text appears in observation entries as illustrative anecdote, not as the object of attention.

## Connections to other threads

This thread is downstream of and adjacent to several others.

- **Perturbation and escape studies.** This thread is a particularly disciplined sub-form of perturbation. Where general perturbation studies ask "what happens to a trajectory under deviations from argmax," steering studies ask the more specific "can a trajectory be directed to a hypothesized destination under bounded perturbation."
- **Basin reachability geometry.** The set of (context-foundation, intervention-specification) → basin mappings is a reachability geometry on the space of basins. Mapping it is a research goal in its own right; this thread contributes by densifying it locally around chosen targets.
- **Crystal hypothesis testing.** The crystal hypothesis predicts that certain basins are stable because of relational density, not sampling accident. Reachability geometry is one of the empirical handles on crystals: a crystal should be reachable from many starting points with relatively small intervention; a contingent basin should require matching prefixes or larger intervention.
- **Sampling at T>0.** Stochastic sampling is a different kind of perturbation — one that perturbs at every step rather than at chosen positions. Comparing T>0 basin reachability to deterministic-intervention basin reachability is a natural follow-up, and the rank-event log layer in records is already shaped for both.

## First concrete experiment, when ready

A sketch, not a commitment. To be refined when prerequisites land.

Pick three already-characterized context-foundations from the first-cycle catalog: one whitespace prefix routing to table-fence basins, one punctuation prefix routing to a boilerplate-opening basin, one less-routed prefix (perhaps `_`). Pick three hypothesized target basins of varying specificity: "any Python code with `def`," "a wiki-article opening about a US president," "a markdown header followed by a numbered list." For each (foundation, target) pair, attempt minimum-intervention steering, recording success/failure and intervention specification. The 3×3 matrix is the first reachability cell of the broader geometry.

This produces nine reachability findings — most likely a mix of trivially-reachable (matching foundation-target pairs), achievable-with-small-intervention, achievable-with-large-intervention, and unreachable. The shape of the matrix is itself the first finding.

## Out of scope within this thread

Even when this thread is running, certain things remain out of scope.

### Discovery of new basins via steering

The thread tests reachability of *hypothesized* basins, not the discovery of basins not previously catalogued. A successful run that lands in an unexpected basin is a side observation, not a finding within this thread; it feeds back into broader basin cataloging.

### Aesthetically-driven targeting

Target basins are specified by structural criteria, not by aesthetic appeal of their produced text. "A basin that produces beautiful nature poetry" is not a target this thread accepts; "a basin that produces text passing a tagged-language-model classifier for English-language poetry with high probability" is acceptable, given a classifier specified in advance.

### Cross-model reachability

Reachability geometries are model-specific in the first instance. Comparing geometries across models is a downstream research thread (covered under "Cross-model comparative taxonomy at scale" in the primary requirements), not within this one.

### Optimization-based intervention search

This thread treats intervention specification as a research question explored by hand and small-scale search. Gradient-based or differentiable-search techniques for finding minimum-intervention paths are deferred — they require treating the intervention specification as an optimization target, which carries its own methodological commitments worth a separate design surface.

---

*This document is downstream of the [Foundations](foundation.md) and a companion to the primary [Design Requirements](design-reqs.md) and the [Records Design](design-reqs-records.md). It specifies a research thread the project will pursue once first-cycle prerequisites are met.*
