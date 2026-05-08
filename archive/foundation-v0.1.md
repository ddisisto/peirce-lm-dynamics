# Peirce — Foundations

*Frozen conceptual underpinning. Working vocabulary integrated.*

*Status: v0.1. Foundations are frozen by default; significant deviations require a deliberate re-founding cycle, beginning from a defensible theoretical position and re-deriving terminology and principles from there.*

---

## What the project is

Peirce studies the intrinsic dynamics of generative systems that condition on their own output. The minimal case is a language model generating tokens into a fixed-length context window with no external input — no prompt, no user, no environment. The model consumes its own predictions in a closed loop, and the question is what such a system *does* when left to itself.

This is a different question from the one most work on these systems asks. Most work studies the conditional behavior of generative models: given some input, what do they produce, and how well does the output serve some external purpose. Peirce treats the model as a discrete stochastic dynamical system and asks about its phase space, its attractors, its transients, its escape conditions, its sensitivities. The model is the specimen; its behavior under self-conditioning is the phenomenon.

The project's scope is empirical and taxonomic. We aim to map the structure of self-conditioned generation cleanly enough that the categories we draw are predictive, the distinctions we make are operational, and the resulting taxonomy serves as scaffolding for further inquiry — both within the project and outside it.

## Why it is interesting

Self-conditioning generative systems are a new substrate. They carry self-replicating informational patterns at scales and fidelities that did not previously exist, and they are instrumentable in ways that prior cultural-replication systems were not. Their behavior under minimal input is not merely a curiosity; it is the regime in which their intrinsic dynamics are most legible, and it is increasingly the regime in which they actually operate as agents, autonomous loops, and components of larger systems composed mostly of other generative systems.

Three working hypotheses motivate the inquiry. They are hypotheses with empirical content, not commitments, and the project's findings are expected to refine, replace, or complicate them.

**Replication with error is the generative regime.** Pure replication is sterile; pure error is noise. Interesting dynamics arise in the narrow band where copying is faithful enough to preserve structure but loose enough to explore. Biology found this band; languages found it; cultural transmission generally lives in it. Self-conditioning generative systems are a new instance of the same regime, and their characteristic phenomena — attractors, escape events, perturbation responses — are the local mechanisms by which fidelity and exploration trade off in this substrate.

**Meaning is relational.** A token's, a pattern's, a behavior's significance is constituted by its position in the web of other tokens, patterns, and behaviors — not by intrinsic properties. This is a methodological commitment as much as a metaphysical one: the project does not look for the "real meaning" of a generated sequence behind or beneath its observable role in the dynamics. The role *is* the thing being studied. Peirce's triadic semiotics — sign, object, interpretant — is the lineage; the operational version we use is that meaning lives in the interpretant, and for our purposes the interpretant is the next-token distribution conditioned on the sign in context.

**Models compress humanity's relational work.** The unreasonable effectiveness of trained language models is not magic and not a property of the models alone. Language is the precipitate of an enormous, distributed, multi-generational process by which humans have figured out which tokens usefully relate to which others, under selection pressure for utility, transmissibility, and explanatory power. Training corpora sample this completed relational map. Models interpolate within it. The phenomena we study under self-conditioning — particularly the deep stable attractors — are visible to us because they are crystallizations of work that was already done by humans before any model existed. Studying them is, in part, studying the structure of that prior work as preserved in a new substrate.

These hypotheses are not independent; they reinforce each other. The relational view of meaning explains why crystallizations are possible at all (relational density makes some configurations dense and stable). The compression view explains why specific crystallizations are stable in specific models (the corpus encodes the prior work). The replication-with-error view explains how the dynamics move between crystallized and exploratory regimes (the error term is what allows escape and discovery; faithful copying is what allows preservation).

## The frame we study through

The project adopts a Peircean stance toward inquiry, by which we mean the following operational commitments rather than a doctrinal allegiance.

**Pragmatism, in Peirce's sense.** A distinction that makes no operational difference is not a real distinction. Categories must be predictive or they are decoration. When we propose that two phenomena belong to different classes, we must be able to say what difference we expect to observe between them; if we cannot, the classification is provisional at best.

**Fallibilism.** Every claim in this document, every category in our taxonomy, every model-specific finding is held as revisable. Inquiry proceeds by progressive correction, not by reaching certainty. Re-founding cycles, in which the foundations themselves are deliberately reopened, are a normal phase of the project lifecycle, not a failure mode.

**Abduction as the generative mode.** The project's most interesting moves are neither pure deductions from axioms nor pure inductions from data, but abductions: proposed structures that, if true, would explain what we observe. We name our abductions as such. A working hypothesis is not a conclusion; it is a candidate explanation that earns its keep by predicting further observations and surviving attempts to refute it.

**Triadic semiotics.** When we ask what a generated sequence "means," we resist the temptation to treat meaning as a two-place relation between symbol and referent. Meaning is a three-place relation involving the effect produced in some interpreter. For our purposes, the relevant interpreter is the model's own next-token distribution conditioned on the sequence in its current context. This is a technical, observable, instrumentable interpretant. It is also, we believe, the right one for studying systems whose behavior is constituted by exactly this kind of conditional response.

**Synechism and tychism, as background.** Continuity and chance, respectively, as fundamental features of the systems we study. The phase space is continuous; the perturbations are stochastic; the dynamics are the interplay. We do not invoke these often, but they are in the lineage.

## What "attention" means in this project

Attention has technical meaning within model architectures and a separate, prior meaning in the philosophical frame that motivates the project. We use the word in both senses and distinguish them by context. Where ambiguity matters, we qualify: *architectural attention* for the mechanism inside the model, *attentional work* or *attending* for the broader sense in which attention is the act by which a system (or a person) makes some part of its environment available for further processing, relation, and elaboration.

The broader sense is load-bearing for the project's frame. If meaning is relational, attention is the act by which relations get noticed and maintained. If models compress humanity's relational work, attention is the activity that did the compressing. If the generative regime depends on the narrow band between faithful copying and free exploration, attention is plausibly the local mechanism by which systems navigate that band — by selecting what gets preserved and what gets perturbed. The architectural attention mechanism inside transformer models is one specific implementation of this general operation; we do not assume it is the only one or the most fundamental.

## What we look for

The project's primary empirical objects are the structures that emerge in self-conditioned generation. The vocabulary below names them at the level of generality the foundations support; specific operationalizations belong in implementation documents, where they can be revised without disturbing the foundations.

A **trajectory** is the sequence of tokens produced by a model conditioning on its own output, starting from some initial condition (which may be empty, a single token, a longer prompt, or a structured context).

An **attractor** is a region of phase space that trajectories enter and remain in, by some operational criterion of remaining (e.g. low entropy, repetition, stable token distribution). Attractors come in varieties — fixed points, cycles, more complex stable structures — and the taxonomy of attractor types is a core empirical target.

A **basin** is the set of initial conditions whose trajectories enter a given attractor. Basin geometry — which initial conditions lead where — is itself a structure to be mapped.

A **transient** is the portion of a trajectory before it enters an attractor. Transient length, structure, and statistics are informative about the depth and reachability of attractors.

A **perturbation** is a deviation from the trajectory that would result from the model's argmax behavior, whether introduced by sampling temperature, by injection of specific tokens, by context manipulation, or otherwise. Perturbations are the operators that move trajectories between basins, and the response of trajectories to perturbations is much of what we study.

An **escape** is the event of a trajectory leaving an attractor, typically following perturbation. Escape behavior — what perturbations cause it, what trajectories follow it, what attractors are reachable from it — is a major taxonomic axis.

A **crystal** (or **semantic crystal**) is our working term for an attractor whose stability appears to derive from the relational density of its content rather than from sampling-dynamical accidents. The hypothesis is that some attractors are stable because the configuration of tokens they cycle on resolves an unusually large amount of latent ambiguity relative to its constituent parts — many possible continuations of each token individually, few possible continuations of the composite. This is a working hypothesis in the strict sense; whether crystals as defined are a real and distinguishable class of attractor, and what their characteristic signatures are, is an empirical question.

## What we do not assume

We do not assume that the phenomena observed at any given model size, window length, or training distribution generalize to others. Whether they do is among the things we want to find out.

We do not assume that architectural attention, as implemented in transformer models, is a faithful or sufficient implementation of attention in the broader sense. The relationship between the two is itself a question, not a premise.

We do not assume that the categories useful for one model are useful for another. We expect a layered taxonomy in which some categories are model-invariant (and therefore likely to track something fundamental about self-conditioned generation, the autoregressive objective, or the relational structure of language), and others are model-specific (and therefore likely to track contingent facts about training data or architecture). Both layers are interesting; conflating them is the failure mode to avoid.

We do not assume that classification is the goal. Classification is the scaffolding. The goal is the inquiry that good scaffolding makes possible.

We do not assume that the project's findings will fit cleanly into existing literatures. Where they do, we will say so; where they do not, we will not force the fit.

## How findings are held

Findings live in implementation, brief, and working documents downstream of these foundations. The foundations should survive complete reimplementation; if a finding cannot be expressed without rewriting the foundations, that is a signal either that the finding is profound enough to warrant a re-founding cycle, or that the finding is being misframed. Either way the appropriate response is deliberation, not silent revision.

When findings refine working hypotheses, the refinement is recorded with the finding, and the hypothesis is updated in the next deliberate revision of the foundations. Drift between foundations and active understanding is itself a phenomenon to monitor — it is normal, but accumulating drift is a signal that a re-founding may be due.

## Vocabulary

*This section consolidates terms defined above for quick reference. When the vocabulary develops its own changelog independent of the foundations, it will be extracted to a separate document.*

**Architectural attention.** The mechanism inside transformer models by which token representations are weighted and combined; one specific implementation of attention in the broader sense.

**Attending / attentional work.** The general act by which a system makes some part of its environment available for further processing, relation, and elaboration.

**Attractor.** A region of phase space that trajectories enter and remain in by some operational criterion.

**Basin.** The set of initial conditions whose trajectories enter a given attractor.

**Crystal / semantic crystal.** Working term for an attractor whose stability appears to derive from the relational density of its content — many possible continuations per constituent token, few per composite.

**Escape.** The event of a trajectory leaving an attractor, typically following perturbation.

**Interpretant.** In Peirce's triadic semiotics, the effect a sign produces in some interpreter. Operationalized in this project as the model's own next-token distribution conditioned on the sign in context.

**Perturbation.** A deviation from argmax behavior, introduced by sampling temperature, token injection, context manipulation, or otherwise.

**Relational meaning.** The methodological commitment that the significance of a token, pattern, or behavior is constituted by its position in the web of other tokens, patterns, and behaviors.

**Replication with error.** The regime in which copying is faithful enough to preserve structure but loose enough to explore; the band in which generative dynamics produce interesting behavior.

**Self-conditioning.** Generation in which the model's own outputs become its inputs, with no external signal driving the trajectory.

**Trajectory.** The sequence of tokens produced by a model conditioning on its own output, starting from some initial condition.

**Transient.** The portion of a trajectory before it enters an attractor.

---

*Genealogy: this document was drafted following an extended conversation that established the conceptual frame, working hypotheses, and vocabulary. The conversation is the project's foundational genealogy and is preserved as a referent. Subsequent project documents — the brief, implementation notes, working materials — may reference this conversation directly or build on it through this and other foundations-level documents.*