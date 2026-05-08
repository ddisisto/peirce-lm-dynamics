# Deprecated terms — grep checklist

*Working list of terms that the v0.2 re-founding retires or sharpens. Used as a checklist for the post-merge sanitization pass. Each entry: the term, its deprecation status, and the replacement (or the context in which it remains valid).*

*Created on the `refoundation` branch alongside `foundation-v2.md`. The grep pass is downstream of foundation-v2 landing and the rest of the doc-refactor sequence; this file is the working memo for that pass and is itself archive-bound once the pass closes (or stays as historical record of the v0.2 vocabulary shift, depending on how the sanitization concludes).*

---

## Retired as population / taxonomic axes (kept only as predicate-firing record)

| Term | Status | Notes / replacement |
|------|--------|---------------------|
| `candidate-basin` (as population label) | retired | The v1 predicate's terminal-event tag is kept on persisted observations as a record of where the predicate fired. Not a basin classification; not a population axis. Trajectory shape (osc_amp, floor_H, period, etc.) is the new partition surface. |
| `window_cap` (as population label) | retired | Same: the architectural-L_arch terminal event survives as a per-observation tag, but the candidate-basin / window_cap split as a population axis is a measurement artifact (findings.md F1). |
| "37 transient trajectories" (the fp16 selection-bias residual) | retired | Not a real partition. The 100 trajectories are studied as a single substrate under shape metrics; the v1 capture status is incidental. |
| "v1-uncaptured" | retired as population label | Same status as the 37; mention only as historical context for why the depth-collapse probe was originally designed. |

## Subsumed by Cycle-1 empirical findings

| Term | Status | Notes / replacement |
|------|--------|---------------------|
| "crystal vs local-success-trap" pair (`ideas.md` 2026-05-01 entry) | subsumed | Roughly maps to R3 vs R1∪R2 in the three-regime taxonomy (`findings.md`). The local-success-trap framing remains conceptually useful as a *mechanism* description (per-step low-friction self-reinforcement) but is no longer the primary partition. |
| crystal as "stability from relational density" (foundation v0.1) | sharpened | Definition retained, but augmented with the falsifiable operationalization: at least one slot whose alt distribution constitutes a coherent prior over a nameable class. |

## Retired roadmap / design steps

| Term | Status | Notes |
|------|--------|-------|
| `basin-v2` (as a roadmap step / detector design direction) | retired | The entropy-floor / logit-gap-floor detector framing was retired by the depth-collapse finding. The branch name persists in git history; the *direction* it named (build a v2 detector to disambiguate v1's residual) is closed — there is no residual to disambiguate at the population level. |
| "v2 detector" / "entropy-floor probe" / "logit-gap-floor probe" | retired | Same. |
| Phase 0 / Phase 1 / Phase 2 / Phase 3 (brief.md cycle structure) | held historical | The phase structure described Cycle 1 as it ran; the documented sequence (broad-shallow → representative-deep → in-fill) is preserved as historical record in `archive/brief.md`. Forward sequence post-v0.2 lives in `findings.md` research moves N1–N5. |
| `design-reqs-refactor` step | dropped (already retired pre-v0.2) | ROADMAP step 2; its retirement predates the re-founding. |

## Vocabulary that survives unchanged

For reference, in case the grep pass turns up false positives. The following terms remain valid under v0.2 with their v0.1 meanings:

- trajectory, attractor, basin, transient, perturbation, escape (the core dynamical-systems vocabulary)
- interpretant, relational meaning, replication-with-error, self-conditioning (the Peircean / framing vocabulary)
- attending / attentional work, architectural attention (the attention-as-noticed-relations vocabulary)
- pragmatism, fallibilism, abduction, triadic semiotics, synechism, tychism (the Peircean stance)

Note: "transient" has both a still-valid sense (the portion of a trajectory before attractor entry) and a deprecated sense (v1-uncaptured trajectories from the Cycle-1 substrate). The grep pass should distinguish.

## New vocabulary introduced in v0.2

For reference, terms that are now load-bearing and should be used consistently going forward:

- **context collapse** — the per-trajectory phenomenon
- **shape (of a trajectory)** — the per-step record timeseries as taxonomic surface
- **shape metrics** — onset, floor_H, floor_gap, osc_amp, period (specific metrics revisable; the umbrella is foundational)
- **phase position / slot / scaffolding** — the within-attractor decomposition
- **slot-readout** — the descriptive operation
- **measurement instrument** — the framing under which a class-enumeration attractor is treated as an observable
- **H-trace** — the per-step entropy timeseries as reading guide

## Sanitization pass scope (post-v0.2 merge)

When the sanitization grep runs:
- Scope: all repo files except `archive/` (which holds historical record), `.git/`, `.venv/`, `data/`, `peirce/` and `scripts/` source where the tag is a legitimate runtime terminal-event label.
- Touch lightly: prefer adding a "*see archive/deprecated-terms.md*" pointer or a one-line note over rewriting passages that are clearly historical context.
- Do not touch: `observations.md` entries (append-only, point-in-time records).
- Do not touch: `archive/*` (held historical by definition).
