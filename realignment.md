# Peirce — Realignment Notes

*A re-founding-cycle document, in the sense [foundation.md](foundation.md) names. Not a revision of the foundations themselves; a record of where the project stands, what frame-level question has been raised, and what move is needed before the next arc is committed to.*

*Status: 2026-05-07. Triggered by an empirical finding on the `basin-v2` branch (state pinned to `596141b`, summarized below) that, on examination, recovers a phenomenon already well-documented in the literature (Holtzman et al. 2019, "The Curious Case of Neural Text Degeneration"). The fact that we arrived at it blind is the trigger; the consequence is that the cartography frame's relationship to existing work needs explicit accounting before further commitment.*

---

## Where the project got to

Cycle 1, as scoped in the (now historical) [brief.md](brief.md) and tracked in [ROADMAP.md](ROADMAP.md), produced:

- A persistence layer (trajectory / observation split, content-addressed identity, KV-cache prefill, runner — merged in `6245a01`).
- A v1 token-cycle basin detector (`basin_capture(K=4, max_period=32, cycle_window=256)`) live at runtime, with its catalog at v0.3 (fp32, frozen as historical record).
- A broad-shallow + selection-bias data substrate at fp16, persisted to `data/peirce.db`.
- On `basin-v2` (5 commits past `0ffe1ee`), a full-depth substrate: all 100 top-from-BOS trajectories materialized to L_arch=2048, predicate-free re-extension stored under `[eos, window_cap]` only, sharing trajectory rows by content-addressed identity with the existing observations.

The branch's intended work — design and implementation of basin detection v2, originally framed as an entropy-floor / logit-gap-floor probe — produced an unexpected finding instead.

## What the data showed

A pre-design calibration probe over the full-depth substrate found that **per-step entropy collapses to near-zero at depth across all 100 trajectories**, regardless of which v1 terminal event their selection-bias observation carries. Population medians in the `[1024, 2048)` window: candidate-basin trajectories at 0.010, window_cap (v1-uncaptured) trajectories at 0.022. Of 96 trajectories that drop below threshold 0.1 with smoothing 8, the median onset positions are 174 (candidate-basin) and 143 (window_cap); 4 trajectories never cross the threshold. Three regimes are visible at depth: phrase-cycle persistence, short-period transitional captures, and very-short capture variability. The full numerical picture is in the 2026-05-07 entry in [observations.md](observations.md), pinned to `1e5710e`.

The immediate operational consequence: the entropy-floor-as-v2-detector framing is retired by the data. Entropy at depth is universal under T=0 self-conditioning on this substrate — it is a depth phenomenon, not a basin phenomenon. The candidate-basin and window_cap populations do *not* separate on this signal.

## The frame-level question this raised

The phenomenon is well-described in existing literature and substantially derivable from first principles:

- **Holtzman et al. 2019**, "The Curious Case of Neural Text Degeneration" — the canonical reference for low-entropy repetitive output under greedy decoding. Motivates nucleus sampling against this exact failure mode.
- **Welleck et al. 2020**, "Neural Text Generation with Unlikelihood Training" — frames the same phenomenon as a training-objective pathology.
- **Su et al. 2022** and contrastive-decoding work — operationalizes degeneration via similarity-to-recent-context.

A priori derivability sketch: under T=0 (argmax) with finite vocab, the trajectory is a deterministic map on the truncated context; deterministic maps on effectively-finite state spaces have absorbing sets; argmax extracts the mode rather than averaging it, so any directional pull in the conditional gets amplified rather than washed out. Entropy-collapse-at-depth is the expected outcome, not an empirical surprise.

We arrived at it blind. The project's foundations and brief never named neural text degeneration as the prior phenomenon against which any cartography would have to position itself. That omission is the trigger for this document.

## What it implies — and does not imply — about the project's frame

It does not invalidate the cartography move. The structural questions Peirce posed — *which* low-entropy structure trajectories enter, *what content shape* it takes, *what basin geometry looks like in content-shape space*, *whether the crystal hypothesis names a real and distinguishable class of attractor* — are not questions Holtzman et al. asked. They observed degeneration to motivate a fix; they did not taxonomize the structures the trajectory enters as targets in their own right. The cartography frame is, in principle, downstream of and additive to the degeneration finding.

It does, however, raise four open questions that need explicit accounting before further commitment:

1. **Is *cartography of self-generated content shapes* distinct from existing work, or a re-framing of it?** We have not surveyed adjacent literature deliberately. There may be cataloging work on T=0 self-generation we are unaware of; there may not be. Until we have looked, we do not know whether the project occupies open ground.
2. **Is the crystal hypothesis empirically separable from existing accounts of degeneration?** What observation would distinguish a "semantic crystal" — relationally-dense low-entropy attractor — from a "high-likelihood absorbing region" of the kind the decoding literature already describes? If no operationalizable distinction can be named, the hypothesis is at risk of being decoration, in the strict pragmatist sense [foundation.md](foundation.md) names.
3. **What does the Peircean / triadic-semiotic frame add over decoding-quality, mech-interp, and dynamical-systems framings of the same phenomena?** The frame is the project's most distinctive feature and also the one whose load-bearing-ness is least verified. If it can be removed without changing what we observe, measure, or conclude, it is decoration; if not, the work it does should be nameable.
4. **Is "self-conditioning generative dynamics" the right scope?** Possibly the right scope is narrower (one specific phenomenon, treated deeply) or wider (something that includes self-conditioning as one case). The current scope was set under priors that have now shifted.

## What is occupied and what is open — partial inventory

Returned blind, before deliberate survey. Treat as a starting hypothesis for the literature pass below, not a conclusion.

- **Entropy collapse / repetition under greedy decoding** — occupied. Holtzman, Welleck, Su, and the broader decoding-quality literature.
- **Dynamical-systems framings of transformers** — partially occupied. Geshkovski et al. 2023 (transformers as interacting particles); attention-as-Hopfield (Ramsauer et al. 2020). Mostly hidden-state level rather than token-trajectory level.
- **Model collapse** (Shumailov et al. 2023) — occupied for a different self-conditioning phenomenon (training across generations on synthetic data); the term "collapse" is taken in a related sense.
- **Repetition / copying / induction circuits in mech interp** (Olsson et al. and subsequent) — occupied at the circuit level for the mechanisms producing the content shapes we observe.
- **Cataloging the structures (cycles, ascends, concats, drifts, templates) of T=0 self-generated text as a taxonomic target** — unknown. This is the place we'd most directly compete or build on. We have not searched for it.
- **Peircean semiotics applied to LM dynamics** — almost certainly absent or fringe. Distinctive, but distinctiveness is not the same as load-bearing.

## What survives any re-founding decision

Independent of how the open questions resolve, the following are durable:

- **The data.** `data/peirce.db` carries 100 trajectories × 2047 materialized steps, content-addressed under the current stack identity. It is reusable under any frame.
- **The persistence layer and runner.** Frame-neutral infrastructure.
- **The observation entries.** `observations.md` is append-only and pinned to commits; entries reproduce regardless of how the surrounding frame moves. Both the original (later-corrected) calibration entry and the depth-collapse confirmation are honest records of the trajectory of inquiry and stand as such.
- **The v1 token-cycle predicate and catalog v0.3.** The catalog is mixed (asymptotes blended with transients, by what we now know) but the underlying predicate is well-specified and the data it produced is reproducible.

What is frame-dependent and at risk under re-founding:

- The basin / attractor / crystal vocabulary, *as a primary taxonomic axis*. The vocabulary may survive; its prominence may not.
- [brief.md](brief.md) and the [design-reqs](design-reqs.md) family. Already held-historical; their operational claims have largely been subsumed by code and per-path docs. A re-founding may retire them outright.
- [ROADMAP.md](ROADMAP.md) step 2 — the basin-v2 step is now mis-named and mis-scoped. Needs revision or replacement after the re-founding decision.
- The catalog ([basins.md](basins.md)) as the project's primary deliverable shape. May be re-cast, re-scoped, or demoted depending on what the re-founding produces.

## Proposed move

Two-step, in order:

1. **Literature survey via research agent.** A deliberate pass against the open questions above, returning citations + abstracts + an honest synthesis of what each finding implies for the cartography frame. Priority targets: structural cataloging of T=0 self-generation specifically; dynamical-systems work at the token-trajectory level; mech-interp circuits for the content shapes we observe; any application of Peircean semiotics to generative models.
2. **Re-founding decision on main.** Based on the survey, choose one of: (a) sharpen the cartography frame against now-explicit company; (b) reposition the project as a synthesis rather than a discovery; (c) admit the marginal value isn't there and pivot to a narrower / wider / different scope; (d) something the survey makes possible that we cannot see from here.

The basin-v2 branch state (596141b) is held pending this decision. Disposition (PR, rework, close-out as record) is downstream of the re-founding.

## Methodology question for the next data arc

Held open here, for resolution as part of (or shortly after) the re-founding decision. Independent of which frame the project lands on, the next data work has a methodology choice that shapes what it produces.

The current data is top-100-from-BOS — the trajectories the model produces under the most restrained possible initial condition. Daniel has named a class of further short-seed work: 1-2 token initial conditions, including selected combinations of words for which there are concrete crystal-shaped predictions. Three modes:

1. **Hypothesis-driven probing.** Pick seeds for which we have specific predictions about whether they crystallize, what they crystallize into, or what perturbation responses they exhibit. Test directly.
2. **Organic continuation.** Extend the minimal-intervention seeding pattern (top-K, low-bias selection rules over a defined seed vocabulary) and see what shapes appear at the population level without bias from prior expectation.
3. **Both, with explicit ordering.** Either organic-first to characterize the prior population, then hypothesis-driven to perturb and test against that characterization; or hypothesis-driven first to sharpen the conceptual frame, then organic to check whether the sharpened frame is representative.

The Peircean frame cuts both ways:

- *Pragmatism* (a distinction must make a predictive difference): if specific crystal predictions exist with named distinguishing observations, testing them directly is the work the foundations explicitly call for. Holding back is methodologically conservative but pragmatically idle.
- *Fallibilism* (priors must be checked, not assumed): hypothesis-driven testing biases what we look for; the population characterization is the safety check against pre-committing to a frame the data does not support.

The right ordering likely depends on what the literature survey returns. If structural cataloging of T=0 self-generation is already populated, organic-first mostly recovers known ground and hypothesis-driven becomes the more efficient first move. If it is not, organic-first establishes the substrate everyone (this project included) needs as a comparison baseline, and hypothesis-driven testing earns its keep against that baseline. Held pending.

---

*This document is itself revisable. It records a state of the project at one point in its inquiry and the open questions held at that point. It will be superseded — by a decision on the open questions, by a new realignment if the survey produces one, or by being absorbed into a future foundations revision if a re-founding is committed to.*
