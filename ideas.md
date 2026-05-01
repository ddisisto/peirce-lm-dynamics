# Peirce — Ideas

*Forward-looking threads worth preserving but not yet formalized into design surfaces. Append-only. Each entry captures key moves of a thread that has emerged but is not ready (or not yet worth) full design-reqs treatment. Entries may later graduate to their own design-reqs companion documents, be absorbed into existing ones, or remain here as durable parking spots.*

*The bar for entry: the thread is concrete enough to lose context if not captured, but abstract enough that committing to its design surface would be premature. Entries below the bar belong in conversation; entries above it belong in design-reqs.*

---

## 2026-05-01 — Transients as the territory of useful generation

A reframe of what basins *are for the project's purposes*, with implications that ripple across multiple existing threads.

### The core observation

Basins are by definition where the model has committed to a stable pattern — repetition of a phrase, a table fence, a fixed point. They are *degenerate* outputs from any usefulness standpoint. Useful outputs of a generative model — code that compiles, prose that informs, a poem that resonates, an answer to a question — are emphatically *not* basins. They are transients: the model is producing them while moving through phase space. The journey, not the destination.

This produces an asymmetry in how basins should be regarded:

- For the **science of self-conditioned dynamics**, basins are the primary phenomena — stable, fingerprintable, the structural features that make cartography coherent.
- For the **engineering of useful outputs**, basins are absorbing failure modes — the points where the model has stopped doing anything useful and committed to a degenerate pattern.

Both framings are legitimate and use the same map for different purposes.

The mechanism by which some transients fail to escape into useful territory — each step being too locally-successful for escape pressure to accumulate — is unpacked in the *EOS as implicit-success signal* entry below, under *The same mechanism at micro-scale: local-success traps*. Productive transients must have non-trivial step-level uncertainty maintaining the possibility of meaningful continuation; degenerate transients lock in when uncertainty collapses prematurely.

### EOS as success state — and the value-judgment that names

Currently the design requirements treat EOS as one of four terminal events, formally symmetric with budget-cap and window-cap (extrinsic) and structurally similar to candidate-basin (intrinsic). For purposeful generation, EOS is the *only* successful terminal.

This is already a value-judgment of sorts: by treating EOS as termination at all, the project privileges the model's own commitment to ending over arbitrary stopping points. That move is defensible because EOS is *model-intrinsic* — the model produced it, it is a fact about the model in this configuration.

Promoting EOS to *success state* would be a substantially stronger move. It imports an external normative criterion (good outputs end intentionally) onto an intrinsic event. This is not obviously wrong — it aligns with how generative models are actually used — but it shifts the project from descriptive cartography to evaluative cartography, with all the methodological commitments that entails. Worth naming as the line being crossed if the project takes this thread seriously.

### Key moves of the thread, if pursued

1. **Transients need their own characterization vocabulary.** Length distributions, productive vs degenerate, fitness profile across the transient, basin-approach rate (how fast certainty rises into a basin), escape pressure (how often the trajectory steps toward escape). Most of this is computable from existing thin records — vocabulary and probe-suite addition, not a schema change.

2. **EOS deserves asymmetric attention.** Map how trajectories arrive at EOS — the certainty profile in the steps approaching it, what context-foundations produce EOS-completing transients of various lengths, what fitness signal correlates with successful completion.

3. **External fitness probes extend the probe interface.** The records design specifies probes as `(window, records) → result`. External fitness — code passes tests, classifier scores text as English poetry, human rates as informative — slots in as probes whose result comes from external judgment. Architecture accommodates this without modification.

4. **Adjudication categorical structure refines.** Currently: "candidate basin → true basin or extended transient." Layered: "EOS with positive fitness," "EOS with negative fitness," "basin-capture (failed to complete)," "budget/window-cap (incomplete due to extrinsic bound)." Refinement of, not replacement for, the basin-vs-transient distinction.

### UI/UX horizon

Tentative, premature to commit to specifics. The latent shape is *navigation* rather than *prompt-and-receive*: a user co-piloting through phase space, with real-time visibility into the certainty profile and basin proximity, intervening at low-certainty steps to redirect before commitment, treating EOS as a navigation event the user confirms. Current LLM UX treats the model as a black-box text producer; a dynamics-aware UX would treat the model as a navigable space the user explores collaboratively. Whether this is the right form factor, or whether it's only useful for specific task classes, is exactly what "the science advances a bit further" needs to answer before any UX commitment is sensible.

### Readiness to graduate

This thread becomes a design surface (its own `design-reqs-transients.md` or absorbed into an evaluative-cartography companion) when (a) productive-vs-degenerate-transient classification becomes formalizable, and (b) external fitness probes have been exercised on real trajectories. Until then it lives here.

### Why park rather than design now

Two reasons. First, the move from descriptive to evaluative cartography is a substantial commitment that deserves to land deliberately, not as a side-effect of cycle-2 work. Second, the methodological discipline that makes this thread non-doom (fitness measured by external criteria specified in advance, transient productivity defined structurally not aesthetically) needs the experience of cycle-1 and cycle-2 work to specify well. Premature design surface here risks bad commitments.

---

## 2026-05-01 — EOS as implicit-success signal in self-conditioned context

A sibling to the transients-as-territory entry above, distinct enough to deserve separate capture. Where that entry frames EOS as success-state of the *current* trajectory, this one frames EOS as success-evidence from *prior* generation, present in the model's own context history. The two halves together form a fuller picture of EOS as a load-bearing token rather than a neutral terminal.

### The core observation

If a model's context contains its own previously-generated EOS markers followed by more content — `[BOS, c1, EOS, BOS, c2, EOS, BOS, ...]` — each EOS-then-continued-context structurally resembles documents in the training corpus where a section completed and the document continued. The model's distribution conditioned on such a context is the distribution of *content that follows successfully-completed sections in documents that survived corpus curation*. The implicit-success interpretation is not a propositional belief the model holds; it is a structural property of the conditional distribution the model is sampling from.

Generalizes beyond EOS: any token or sequence the training distribution treats as a section-completer (a closing code fence, a markdown horizontal rule, a multi-token basin pattern we have catalogued) carries the same structural signal in proportion to how strongly the corpus treats it as section-closing.

### Why this is grounded in the training distribution

The training corpus is documents that *got included*. Multi-section documents — chat logs, FAQs, document concatenations, multi-message threads, code files with multiple functions — are the structures where section-completion is followed by more content. The model has learned that "section-completer then continuing context" is the structural shape of material that survived selection enough to be assembled into the corpus. The "success" signal is structural and grounded in the curation process that built the training distribution, not a learned reward.

### Loss as friction; self-generation as minimum-friction expression

The argument tightens when we add that self-generated output (under low temperature, especially T=0) is the model's *minimum-friction* path through its own distribution. Training loss is literally the surprise the model has at observed tokens; the model's generated trajectory at T=0 is the trajectory of minimum per-step surprise. Self-generated EOS-bracketed completions are therefore not arbitrary content — they are the model's own low-friction expression of what completed work in some style looks like.

When the model encounters its own previous EOS-bracketed work in its context history, it is seeing a record of minimum-friction completion. This is a stronger success signal than mere structural-resemblance-to-corpus: it is evidence that the model can produce this kind of work *while expending little surprise*, which correlates closely with whatever the training process selected for as fluent and well-formed output.

The triad: loss is the model's own measure of cost; self-generation is the model's minimum-cost trajectory through its distribution; EOS-marked self-generated context is a record of past minimum-cost completion that the model treats as evidence of further minimum-cost work being available in the same style.

This is also the cleanest answer to "why is self-generated output qualitatively different from arbitrary same-style text injected into context?" It is different *because* it is the low-entropy version of the model doing the thing — a direct expression of the model's own fitness landscape, where loss is friction and self-generation is the path of least friction.

### The same mechanism at micro-scale: local-success traps

The success-signal-in-context interpretation generalizes from EOS-marked section boundaries down to every step of generation. A model that has produced any token and seen it followed by more context has structural evidence that producing that token was correct — the trajectory continued, no termination intervened. Every step is its own micro-success-signal.

This explains a class of degenerate outputs that have a unified mechanism: ascending numeric sequences (1, 2, 3, 4, ...), ordinal cascades (first ... second ... third ...), repeated table fences, bullet-point cascades, repeated opening phrases ("the first thing to note is that..."). In each case the next step's continuation is *over-determined* — the friction-minimum is so far ahead of all alternatives that escape pressure never accumulates. Each locally-successful step provides positive feedback for continuing the pattern. Opening tokens are particularly trap-prone: "first" is the friction-minimum at the start because nothing came before it, and once "first" has been followed by more text the model has evidence that opening-tokens-here-are-correct, producing another "first" and closing the loop.

This identifies a second basin family, distinct from the crystal hypothesis named in the Foundations:

- **Crystals** (hypothesized): stability from *relational density* of content. Many continuations per constituent, few per composite. Rich.
- **Local-success traps** (named here): stability from *per-step low-friction self-reinforcement*. Each step is the obvious continuation of the immediate prior context; escape pressure never builds. Thin.

These have different predicted signatures and should respond differently to perturbation. A crystal should be robust to small perturbations because its relational density is the source of stability — the basin holds together as a structure. A local-success trap should escape readily under almost any perturbation that breaks the immediate-prior-context dependency — there is no rich structure holding it together, only the local feedback loop.

The first-cycle observations already span both. Whitespace-to-table-fence trajectories and the "_first_ thing to note" basin from trajectory 28 are textbook local-success traps. The Chromium-browser period-11 phrase basin (rank 0, representative-deep) might be either; distinguishing requires perturbation response, not just structural observation. The crystal-vs-trap distinction becomes a real cataloging axis when basin formalization lands in Phase 2 — it is one of the first cuts a basin taxonomy should support.

### Testable predictions

- Trajectories from `[BOS]` differ measurably from trajectories from `[BOS, content, EOS, BOS]` for the same model — likely more committed, lower entropy throughout, more strongly biased toward continuing in the prior content's mode.
- The effect should accumulate with multiple EOS-separated sections in the prefix: `[BOS, c1, EOS, BOS, c2, EOS, BOS, c3, EOS, BOS]` should produce content statistically related to the c_i, with the relationship strengthening as the prefix grows.
- Self-generated content as the prior c_i should produce stronger effects than externally-supplied content of the same style, because of the friction-as-fitness mechanism above. This is the cleanest test of the loss-as-friction half of the argument.
- Stop-tokens that are not EOS but are treated by the corpus as section-closers (closing code fences, horizontal rules, certain multi-token basins) should produce structurally similar effects when present in context history, scaled by how strongly the training distribution treats them as section-closing.
- Mixing EOS-marked prior work with novel prompts should be a steering technique with measurably different efficiency than novel prompts alone.

All of these are runnable on the existing engine with no schema changes; the only new requirement is convention support for EOS-laden initial conditions.

### Connection to other threads

- **Transients as the territory of useful generation** (entry above): companion frame. Together they form a more complete picture of EOS as load-bearing token.
- **Steered trajectories** (`design-reqs-steering.md`): EOS-bracketed context becomes a high-leverage prefix structure. Injecting self-generated "successful" sections as part of a context-foundation is a steering technique with structural and friction-based grounding.
- **Convention sensitivity** (`design-reqs.md`): `[BOS, content, EOS, BOS]` initial conditions, parameterized by the content placed before and by whether that content was self-generated or externally supplied, are a meaningful new axis of starting condition. Worth a paragraph in the convention-sensitivity section when `design-reqs.md` is next touched.

### Multi-context architecture sketch

A speculative engineering direction worth naming. Branch off contexts to implement specific deliverables; each branch produces output ending in EOS; recombine outputs into a shared context that contains many EOS-marked completed sub-tasks. The recombined model samples from "what follows several successfully-completed sub-tasks of this kind," structurally biasing toward continuing to produce more such sub-tasks. The success signal lives in the structural pattern of the context, not in any explicit reward model.

This is structurally adjacent to in-context few-shot learning but sharper. Few-shot examples teach the model *what kind of thing to produce*; EOS-bracketed self-generated prior outputs teach it *what kind of thing to produce, plus this is the low-friction kind of thing for me to produce, plus the structural shape resembles content that has been selected for in my training*. The combination imports several distinct selection pressures into the active context simultaneously.

If real and large-effect, this is a way to bootstrap self-reinforcing productive generation that does not require an explicit reward model.

### Cautionary note: structural, not evaluative

The success signal is structural — it tracks "this pattern resembles ones that survived corpus curation" and "this content is low-friction for the model to produce." It does not track "this content is good in any external sense." A model whose context fills with its own EOS-marked outputs is in a self-reinforcing loop regardless of whether those outputs are externally valuable. This matters for any architecture built on the multi-context sketch above: structural success is not the same as fitness-on-task, and conflating the two is a real failure mode worth naming explicitly.

This caution does not undermine the insight; it sharpens it. The structural success signal is real and measurable; whether to treat it as a proxy for external fitness is a separate decision that requires external fitness probes (see transients-as-territory entry above).

### Readiness to graduate

Several pieces of this can move forward immediately within current capabilities — the testable predictions are runnable on the existing engine with the convention extension for EOS-laden initial conditions. Whether the thread graduates to its own design surface depends on what the predictions show. If the EOS-in-context effect is large and measurable, it joins steering as a primary mechanism and likely earns its own design surface (perhaps `design-reqs-conventions.md` covering the broader axis of context-shape effects). If the effect is small or model-specific, it stays here as a documented direction not pursued in cycle 1.

---

*This document is downstream of the [Foundations](foundation.md) and adjacent to the design requirements suite. Threads here are pre-commitment; entries should be as careful in capturing reasoning as design surfaces are in capturing requirements, because the reasoning is what makes the thread re-enterable later.*
