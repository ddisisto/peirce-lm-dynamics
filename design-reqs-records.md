# Peirce — Records, Windows, and Observation Design Requirements

*Companion to the primary [Design Requirements](design-reqs.md). Specifies what observations the project records, how they are structured, and how they are read. The structure of recorded observations is load-bearing for everything downstream — storage, reproducibility, findings discipline — and warrants its own document.*

*Status: v0.1. Revisable; revisions recorded. Foundations supremacy applies.*

---

## What this document is

The primary design requirements specify what the project must do. This document specifies *what gets recorded when it does it*, and *how those recordings are read*.

It exists because three concerns coalesce into a single design surface:

- The structure of per-step records and trajectory packets — what fields, in what layers, with what canonical status.
- The role of windows as named selectors over trajectories — the act of choosing where to look at a recording is itself an observational act.
- The relationship between recorded certainty and reproducibility — what a reader on different hardware can trust, and what they cannot.

These cannot be specified independently without redundancy. They are specified together here.

This document supersedes the per-step records and provenance handling sketched in the primary design requirements; the primary doc references this one at the points where record structure is load-bearing.

## Hardware nondeterminism, briefly

Floating-point matmul on different hardware produces different logits at the bit level. Argmax — the choice of next token under hard-cap T=0 — agrees across systems wherever the rank-1 / rank-2 logit gap exceeds the system's numerical noise floor (typically ~1e-3 to ~1e-4 in fp32, depending on stack), and may disagree where the gap is below the noise floor. A single rank-1/rank-2 flip at any step diverges the trajectory from that step onward under self-conditioning.

This is not a defect to be engineered around. It is a property of the substrate. The records design accommodates it: dense token records are ground truth on the system that produced them, certainty annotations predict where divergence between systems is plausible, and reproducers compare recorded sequences to their own runs at predicted-fragile sites.

Bitwise cross-system reproducibility is deferred — see *Out of scope* below.

## The observation packet

A trajectory observation is a packet, not a sequence. The packet carries:

- **Stack identity.** Model id and revision; dtype; device; deterministic-flags state; library versions sufficient to characterize the producing system.
- **Initial condition.** The token-id sequence the trajectory was launched from, recorded explicitly (not as "default BOS" — as the actual token-ids).
- **Predicate set.** The terminal predicates active for this run, by name and parameters.
- **Inference strategy.** Hard-cap, sliding variants when those become live, etc. — with parameters.
- **Thin records.** The per-step canonical layer. See below.
- **Rank-event log.** Sparse list of non-argmax events: positions where T>0 sampling produced a non-rank-0 token, or where injection placed a specific token. Empty under T=0 hard-cap with no injection.
- **Terminal event.** One of EOS, candidate-basin, budget-cap, window-cap — and its position.
- **Aggregate certainty.** Probe outputs computed over named windows, attached to the packet for convenience but reproducible from thin records.

The packet is the citable unit. References to a trajectory reference the packet.

## Thin records — the canonical layer

Per-step thin records are the only canonical layer. Everything else in the packet is either metadata (stack, initial, predicates) or derived (rank-event log, aggregate certainty).

Each step carries:

- **Token.** Id and decoded string of the chosen token.
- **Log-probability of the chosen token.** How confidently this step was committed.
- **Distribution entropy.** Bulk distributional uncertainty at this step.
- **Alt token and alt probability.** The most-probable non-chosen alternative — under T=0 this is rank-1 by construction; under T>0 sampling or step-0 override this is the model's argmax preference where the chosen token is something else. Same field shape across regimes.
- **Rank-1 / rank-2 logit gap.** The numerical-noise margin at this step. Predicts where cross-system argmax flips are plausible.

Five fields are the analytic instrumentation; the sixth (logit gap) is the reproducibility instrumentation. Both are cheap to capture per step and load-bearing for adjudication and reproducibility respectively.

Single-step characterizations of the model (the predicted next-token distribution at any context appearing in the trajectory ensemble) remain a derived view of thin records, as specified in the primary design requirements. Adding the logit-gap field does not change that.

## Dense canonical, layered annotations

The dense token sequence is ground truth on the system that produced it. The rank-event log is a perturbation/sampling annotation layered on top: at T=0 it is empty, under T>0 it lists non-argmax sampling events, under injection it lists placed tokens. The annotation layer extends the representation to stochastic and prefixed regimes without changing the schema of records.

A reader who wants to know what the trajectory *was* reads the dense token sequence. A reader who wants to know which steps were *deviations* from argmax reads the rank-event log. Both are present in the packet.

The fully-sparse alternative — storing only the rank-event log and reconstructing tokens from it — would require bitwise cross-system reproducibility we do not have. See *Out of scope*.

## Windows as first-class observers

A *window* is a named selector over a trajectory. The act of choosing a window is the act of placing observational attention on the trajectory: where in the sequence are we looking, and why there.

Windows are first-class objects, not implicit parameters. Common selector shapes:

- **Index-based.** `[:64]` (early), `[-64:]` (late), `[-256:]` (recent), `[k:k+w]` (slice).
- **Predicate-based.** Steps where alt_prob exceeds a threshold; steps where entropy is below a threshold; steps where the chosen token is in a class.
- **Event-based.** From the terminal event back to the last entropy-rise; the segment between two named markers; the transient before a candidate-basin tag fires.

Windows compose: predicate-on-window, slice-of-event-window, etc.

A *probe* is a function `(window, thin_records) → result` — an aggregation, a detector, a statistic. Cycle-period detection is a probe; mean log-prob is a probe; basin-capture adjudication is a probe. Each probe is named, parameterized, and reported with its window.

## Reporting discipline

Every claim about a trajectory names the window and probe that produced it.

- Not: *"Trajectory T cycles."*
- Yes: *"Trajectory T shows period-9 cycle in window `last-256` under probe `tail_cycle(max_period=32)`."*

Same trajectory under different windows can produce different findings without contradiction. That is the structure, not a bug. The Peircean operational commitment carries through: a finding's content is constituted by where attention was placed when it was observed, and naming the window is naming part of the finding.

## Reproducibility framing

Dense token sequences are ground truth on the system that produced them. Certainty annotations — per-step (log-prob, entropy, alt-prob, logit gap) and aggregate (probes over windows) — are the reproducibility prior.

A reproducer with the same model + initial + predicates + inference strategy:

- Re-runs and compares their token sequence to the recorded one.
- High aggregate certainty, matching reproduction → load-bearing claim, generalizable across the configurations that share this certainty profile.
- High aggregate certainty, diverging reproduction → real finding about stack difference. Rare and informative; a divergence at high certainty is evidence of a meaningful nondeterminism source, not a mark against the original observation.
- Low aggregate certainty → recorded as anecdotal at single-trajectory scale, structural at population scale. The trajectory is one sample of a fragile region; what matters is the distribution.
- Low local certainty at a specific divergence site → the model's decision surface there is genuinely close to a coin flip. The site is interesting in its own right and warrants per-step attention.

The certainty annotation does double duty: it self-describes the packet's reliability for a reproducer, and it tells the project's own analysis where to direct attention. This conflation is intentional and useful.

## Cartographic steering

Where attentional work flows is determined by certainty signals.

- **High-certainty regions** are surveyed at scale. Broad sweeps, ensemble statistics, structural summaries. Many trajectories, shallow per-trajectory attention.
- **Low-certainty regions** are read deeply. Per-step inspection of decision surfaces, careful narrative of how the model's distribution shifts step by step, examination of the alt-token trace.

The same machinery — windows + probes — supports both modes. Broad sweeps use coarse windows and aggregating probes; deep reads use fine windows and inspecting probes. The choice is not architectural, it is methodological, and the records design lets it be made on a per-question basis.

This principle also has projection into the primary design requirements: it shapes which trajectories warrant representative-deep extension, which warrant in-fill, and which warrant per-step hand-reading.

## Storage implications

The persistence layer is not specified here, but several implications constrain it.

- **Thin records are append-only and complete.** Once a trajectory terminates, its thin records are the canonical record. Probes and aggregates are derived; storing them is caching.
- **Stack identity is part of the manifest.** Two packets with the same model + initial + predicates but different stacks are different packets. The manifest records the stack.
- **Rank-event logs are sparse and small.** Under T=0 they are empty; under T>0 they scale with sampling events; under injection they scale with injection points.
- **Window and probe definitions are versioned independently of trajectories.** A new probe added later operates over old thin records without invalidating them. Old probes whose definitions change are renamed or revisioned, not silently mutated.

These together suggest a two-tier shape — definitions canonical, records dense, derived views cached — which is the storage direction the project is heading. Specifics are downstream.

## Out of scope (named, deferred)

### Fully-sparse-rank-as-primary-identity

Storing trajectories as `[(position, rank), ...]` alone, with tokens reconstructed by forward-pass on read, is a clean and compact representation. It requires bitwise reproducibility of argmax across the systems that write and read — a precondition the project does not currently have. Deferred until either (a) the project commits to a single deterministic system end-to-end, or (b) cross-stack bitwise reproducibility becomes available. The current design (dense canonical + rank-event annotation) is forward-compatible with adopting fully-sparse later.

### Cross-stack bitwise reproducibility

Achieving bitwise-identical logits across hardware/library combinations is achievable in principle (deterministic algorithms, fixed kernels, fixed dtype, no TF32, controlled reduction order) but engineering-heavy. Not pursued in the first cycle. If pursued later, the records design accommodates it — the logit-gap field becomes a margin-of-safety measurement rather than a divergence-prediction.

### Persistence-layer specifics

What the storage backend looks like — file formats, indexing, query surface — is downstream of this document. The design requirements above constrain it; they do not specify it.

### Cross-trajectory probes

Probes that operate across multiple trajectories — basin-membership clustering, transition-graph construction, ensemble-level statistics — are a real category and will need their own probe interface. The single-trajectory probe interface specified here is the foundation; cross-trajectory probes are deferred until the single-trajectory case is exercised.

---

*This document is downstream of the [Foundations](foundation.md) and a companion to the primary [Design Requirements](design-reqs.md). It assumes familiarity with both.*
