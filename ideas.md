# Peirce — Ideas

*Forward-looking threads worth preserving but not yet formalized into design surfaces. Append-only. Each entry captures key moves of a thread that has emerged but is not ready (or not yet worth) full design-reqs treatment. Entries may later graduate to their own design-reqs companion documents, be absorbed into existing ones, or remain here as durable parking spots.*

*Cycle 2. The cycle-1 ideas.md is preserved as `archive/ideas-cycle-1.md`; threads from there that re-enter the working surface should be restated in current-cycle voice rather than carried forward in retired vocabulary.*

---

## 2026-05-10 — Ivgi 2407.06071 ("From loops to oops") as finer-grained repetition precedent

Cited by Zekri 2410.02724 as the in-practice reference for repetition behaviour: "This behavior is well known and occurs frequently in practice with many existing LLMs (Ivgi et al., 2024), requiring adding a repetition penalty." Title — *"fallback behaviors of language models under uncertainty"* — suggests the paper may decompose loop behaviour at finer granularity than either Geng 2603.11228 or Zekri itself.

Pre-cleared by hand at the close of the regime-vocabulary canonisation pass (commit pending): conceptual overlap with the slot/scaffolding decomposition is at coarser granularity, not specific enough to warrant terminology revision. The catalog's tag set (`SLOTTED` / `SCAFFOLD` / `NOPERIOD` with sub-types) is settled and the precedent map for it is adequate against Geng + Zekri.

The thread is parked here as fascinating-but-not-pressing — worth a focused read in a future precedent pass when there's a substantive question to bring to it. Plausible occasions: when N2 alternate-path continuation results land and the response of the regime tags to perturbation might benefit from a direct comparison to Ivgi's "fallback behaviour" decomposition; or when a future cycle's working surface intersects "uncertainty-driven fallback" as its own phenomenon.

*2026-05-11 update.* N2 first batch landed (`680ccd1`, observations.md entry). With the basin-switch-as-modal-outcome reading in hand, Ivgi's fallback-behaviour decomposition is now a concrete forward thread — the project's "principled axis perturbation produces a different attractor more often than within-attractor exploration" claim wants comparison against whatever finer-grained taxonomy Ivgi proposes for fallback behaviour under uncertainty. Promote to a focused-read task whenever the precedent pass for the N2 results is scheduled.


## 2026-05-11 — "Leverage candidate" language wants softening in `design-reqs.md`

The C2 branching protocol's framing in `design-reqs.md` calls the principled axis (lowest `gap_over_H`) the "leverage candidate" generator, with the implicit prediction that perturbation at these positions redirects the trajectory. The N2 first batch (observations.md entry pinned to `680ccd1`) shows the axis generates positions where outcomes vary widely across the {re-absorbed, wandering, basin-switch} classifier, not positions of one specific behaviour. Cluster A controls and SLOTTED-CLASS textbook bifurcation moments both re-absorb (via different mechanisms); SCAFFOLD and COUNTER specimens basin-switch across `T_req` ranges; the same `gap_over_H` value can produce opposite outcomes in different regime contexts.

The protocol's mechanics still hold (start at principled-axis positions; classify outcomes empirically). The language softening wants: drop "leverage candidate" as the axis's name; replace with something like "principled-axis candidate" or "high-uncertainty candidate" without an outcome prediction embedded in the name; surface that leverage is a (position, attractor) interaction, not a position property.

Parked here rather than landed because the revision wants more data — particularly second-batch under Gumbel-Top-k (per-position K-fan-out outcomes; informative on whether the heterogeneity-under-single-alt of the SLOTTED-HARMONIC bucket is rank-2-specific or robust across plausible alts) and transient-window perturbations (the design-reqs "transient leverage" question, untouched by the first batch). When both threads have data, the wording can land cleanly. Until then, the deferred-language guard is the entry-level discipline: don't propagate "leverage candidate" into new docs.
