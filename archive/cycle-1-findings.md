# Peirce — Findings (2026-05-07)

*A consolidated working document. Captures the 2026-05-07 session's findings, the resulting taxonomic shift, a draft of the updated basin catalog, and project-level implications. Companion to [`realignment.md`](realignment.md): where realignment named open questions and a frame-level uncertainty triggered by the depth-collapse finding, this names a finding that bears on those questions and gives the cartography frame falsifiable empirical content. Held as a single working file pending the structural refactor of repo docs that the finding implies.*

*Status: 2026-05-07. Branch `plots` off `basin-v2` off `main`. Full numerical and visual content reproducible from `data/peirce.db` plus `scripts/plot_trajectories.py` and `scripts/high_h_readout.py`.*

---

## Provenance

- `main` at `6245a01` — persistence layer landed; v0.3 catalog frozen as historical record (fp32). Project default fp16.
- `basin-v2` at `596141b` — pre-design calibration probe over the persisted store + full-depth extension to L_arch=2047 + entropy-onset analysis + 2026-05-07 observation entry confirming the depth-collapse finding (entropy at depth is universal under T=0 self-conditioning on this substrate; v1's candidate-basin / window_cap populations don't separate on entropy or logit-gap signals).
- `realignment.md` (untracked at the time of writing) — re-founding-cycle document raising the question of whether "cartography of self-conditioning generative dynamics" is empirically distinct from prior degeneration work or a re-framing of it.
- `plots` (this branch) — figures over the persisted full-depth substrate, then the high-H readout, then the three-regime taxonomy and Regime-3-as-measurement-instrument framing.

## Methodology

This work is descriptive over `data/peirce.db` (100 fp16 trajectories × 2047 materialized steps, top-from-BOS under hard-cap T=0). No model loading, no inference. All findings are read-only over the existing persistence layer; the population is the substrate built by `broad_shallow.py` + `selection_bias.py` + `full_depth_extension.py`.

Two scripts (read-only renderers, both `uv run python scripts/<name>.py`):

- **`scripts/plot_trajectories.py`** — matplotlib renderings under `data/plots/`: `trajectories_aggregate.png`, `trajectories_shape.png`, `trajectories_outliers.png`, `trajectories_grid.png`. Per-trajectory shape metrics computed from the deep window [1024, end).
- **`scripts/high_h_readout.py`** — top-N highest-H positions per trajectory in the deep window, with chosen / alt / context tokens. The descriptive half of the slot-readout experiment.

Per-trajectory shape metrics introduced this session:

- **`onset`** — first position holding below H<0.1 for 8 consecutive steps (collapse speed).
- **`floor_H`, `floor_gap`** — median entropy, median logit gap over the deep window.
- **`osc_amp`** — std of entropy over the deep window (oscillation amplitude).
- **`period`** — dominant lag from autocorrelation of mean-subtracted deep-window entropy (None when variance is below noise).
- **`gap_over_H`** — `floor_gap / max(floor_H, ε)`. Commitment ratio at the floor.

---

## Findings

### F1. The candidate-basin vs window_cap split is a measurement artifact

The v1 detector's terminal_event labels (candidate-basin: 63, window_cap: 37 in the n=100 fp16 substrate) classify *where the predicate happened to fire*, not anything intrinsic to the trajectories themselves. At depth, both populations:

- Collapse to the same entropy floor (median floor_H: candidate-basin 0.010, window_cap 0.022 — within the same order of magnitude as fp16 reduction-order noise).
- Sit on the same per-trajectory (floor_H, floor_gap) curve (Fig. `trajectories_aggregate.png` panel F).
- Have indistinguishable shape-metric distributions across `onset`, `osc_amp`, and `period`.

The split has been retired as a population axis. Shape metrics replace it. v1's terminal_event values are kept on the persisted observations as a record of predicate-firing, not as a basin classification.

### F2. The (H, gap) per-step relationship is a 1-D manifold

The per-step (entropy, logit_gap) hex density across all ~205k steps shows a clear L-shape: a dense corner at H≈0, gap≈10 (collapsed states); a sparse arc tracing from H~3, gap~0 down to the corner (transient). Per-trajectory deep-window (floor_H, floor_gap) lies on a near-monotonic log-log curve (Fig. `trajectories_shape.png` panel E).

Implication: the **gap/H ratio** is not an information-rich axis once you know either coordinate. What carries information is *position along the manifold over time* — i.e., how a trajectory wanders along the (H, gap) curve. `osc_amp` is the simplest scalar capturing that wandering.

The manifold itself is plausibly a softmax-shape constraint: given a probability distribution over a finite vocabulary, both H and gap are functions of the dominant-mass profile, so they're tightly coupled. The taxonomic signal is *not* in the coupling but in how trajectories move along it.

### F3. Three-regime taxonomy of self-conditioning attractors at depth

The data supports a clean three-way split among attractor regimes, observable from per-step (entropy, logit_gap) plus phase-position chosen-token analysis. Provisional regime names:

#### Regime 1 — *pinned cycles* (osc_amp < ~0.005)

Token-level deterministic loops with no internal slot structure. The trajectory cycles on the same short token pattern; no class to read out. Examples from the n=100 substrate:

- `48a8a855` — table-divider glyphs `---+---+---+`
- `06e46d02` — URL path fragment `/1/roles/1/`
- `40380189` / `9a2c70a8` — checkbox patterns `[x] [x] [x]`
- `28657567` — JSON tokens `string\string\string`
- `eec153e5` — pinned NCBI URL fragment

Approximate count in n=100: ~42.

#### Regime 2 — *mode-locked structural attractors* (osc_amp 0.005–0.05; alt_prob at high-H positions < ~0.01)

Template structure with phase positions that *should* admit class members, but the prior at those positions has collapsed to one mode. The chosen token at a given phase position is the same on every recurrence; the alt is a deeply unfavored runner-up. Template is real; prior readout is degenerate. Examples:

- `d8e73c51` — HackerNews comment thread, mode-locked username "jamesblonde". The username slot is a structural class slot (any HN username could fit) but the model is fully committed to one. alt_prob ≈ 0.015 every recurrence.
- `134c9875` — same template, locked on "joshu".
- `fe8a36a8` — same template, locked on "jimmy1".
- `f0a9edaa` — Nintendo wiki paragraph cycle: `\nThe original game was released…` recurring with alt='Q' at p≈0.007.
- `7dbde4ff` — code-explanation prose `You can also return a reference to…` recurring with chosen='You', alt='The' at p≈0.008.
- `d728e9bd` — government-news prose `The government has also announced…` with alt='This' at p≈0.001.

Approximate count: ~25–30 within the STRUCTURED tag.

#### Regime 3 — *class-enumeration attractors* (osc_amp > ~0.05; chosen-token rotation across recurrences)

Template structure where phase positions admit multi-modal class-prior distributions, with the chosen tokens visibly *rotating* across recurrences. These are the **measurement instruments**: their phase-position alt distributions are direct readouts of the model's prior over the slot's implicit class. Examples:

- `7ce033c6` — **medical conditions enumeration**. Slot rolls through "Chronic heart disease" / "Chronic liver disease" / "Chronic kidney disease". Chosen rotates among `Ch` (with continuation differing at the disease-name token); alt 'Di'. Class: chronic diseases.
- `05677c58` — **ordinal-day enumeration**. `the [DAY] day of the month, the` with chosen rotating through ` nine`, ` sevent` (→ "seventieth"), ` thirty`, etc. Tokenization splits the day-name across `nine`/`th`, `sevent`/`ieth`. Class: days of month.
- `11b07bda` — **counting enumeration**. `The [N]-first thing to note is` with chosen rolling through ` twenty`, ` thirty`. Class: counting words.
- `d58ffabc` — **paper baselines list**. `**Baseline [N]:** We …` with N = 41, 42, 51, 61, 65 across recurrences. Class: numerical baselines.
- `e1069ae4` — **patent template**. `The first|second|contact conductive layer forming process includes a`. alt_prob ~0.25. Class: ordinal-or-named-component.
- `1453d66b` — JSON product catalog with `52|51% Off` percentage slot at H≈3.4 plus randomized hash slots at H≈4–5.
- `e1afc61b` — academic paper Current Address footer `[^36]: Current address:` rolling through reference numbers 36–41.

Approximate count: ~20–25 within the STRUCTURED tag.

#### Regime separator (the falsifiable seam)

Regime 2 vs Regime 3 is distinguished, in principle, by a single statistic per attractor: **chosen-token entropy across recurrences at a given phase position**. Regime 2 attractors have ~0 chosen-entropy at every phase (model picks the same token every time). Regime 3 attractors have non-zero chosen-entropy at one or more phases (the slot positions). This is computable read-only over the existing data once cycle period is known.

### F4. The crystal hypothesis sharpens to a falsifiable claim

`foundation.md` defines crystal as "an attractor whose stability appears to derive from the relational density of its content rather than from sampling-dynamical accidents". The original definition was philosophically motivated but, as `realignment.md` flagged, not empirically separable from "high-likelihood absorbing region" as the decoding-quality literature describes it.

The session's finding gives a separability test:

> **A semantic-crystal-as-measurement-instrument is a Regime-3 attractor: an attractor with at least one phase position whose chosen-token distribution across recurrences is non-degenerate, with the alt distribution at that position approximating the model's prior over a nameable class.**

Properties:

- **Falsifiable.** A given attractor either has rotating chosen-tokens at some phase or it doesn't; the alt distribution at that phase either does or does not constitute a coherent prior over a nameable class.
- **Predictable from the seed.** With a class-enumeration template seed (`The most important novelists are: `), the resulting attractor's regime can be predicted before the trajectory runs.
- **Not (to current knowledge) named in the degeneration literature.** Holtzman 2019 and successors observed degeneration as a quality failure to suppress; they did not partition the regimes by readability. The Regime-1/2/3 distinction does not appear in the cited prior work.

If the predictability holds up under deliberate testing, the cartography frame's marginal contribution is no longer "we found degeneration" (we didn't) but "we found that some degenerate regimes are measurement instruments and some aren't, and the difference is testable." That is a thing.

### F5. Reading the H-trace as attentional alignment

The H-trace per trajectory functions as a *reading guide*: high-H positions are where the model's prior is being read out (slot fillers); low-H stretches are where its template is executing (scaffolding). When humans align reading-attention with high-H positions in Regime-3 attractors, we read the model's prior over a class — a tractable operationalization of triadic semiotics with the human reader as a third-order interpretant of a trace whose first-order interpretant is the model's own next-token distribution.

The pragmatist guard against circularity (per `foundation.md`'s commitment that distinctions must make a predictive difference): the H-trace is computable from the trajectory alone, before any human reads anything. Predictions of slot positions and their class memberships are made before the reading and checked against it. If "high-H is where the interesting tokens are" can only be observed retrospectively, we are free-riding on our own pattern-matching. The seeded class-enumeration experiment (N3 below) is the place this earns its keep.

This is also what gives Regime-3 its operational distinctness: the prediction can be made and checked. Regime 1 has no slot positions to read; Regime 2 has slot positions but the prior at them is degenerate; Regime 3 has slot positions with prior structure that is recoverable, predictable, and not decoration.

---

## Updated basin catalog (v0.4-draft)

The v0.3 catalog (basins.md, fp32, cycle-token-id-tuple keys) is held as historical record. The three-regime taxonomy supersedes its categorical structure; basin identity for Regime-2/3 attractors plausibly wants a structural-template + slot-class fingerprint rather than a token-id tuple. Re-cataloging is deferred until the phase-aware analysis (N1 below) lands a per-attractor regime + slot-class tagging.

Provisional per-specimen regime assignment (subset of n=100, sorted by `osc_amp` descending; full table at end of document):

| oid (8) | osc_amp | regime | shape sketch |
|---------|---------|--------|--------------|
| 1453d66b | 0.407 | R3 | JSON product catalog, percentage + hash slots |
| d8e73c51 | 0.384 | R2 | HN comment thread, mode-locked "jamesblonde" |
| e1afc61b | 0.312 | R3 | academic Current-Address footer, reference number rolling |
| fe8a36a8 | 0.253 | R2 | HN comment thread, mode-locked "jimmy1" |
| **7ce033c6** | 0.250 | **R3** | **medical conditions enumeration (heart/liver/kidney)** |
| **e1069ae4** | 0.221 | **R3** | **patent template, first/second slot** |
| 134c9875 | 0.166 | R2 | HN comment thread, mode-locked "joshu" |
| b9cfdf7b | 0.140 | R3 | narrative dialogue, quote-punctuation slot |
| 62498529 | 0.121 | R2 | JSON `_name_name_name` template |
| 1a4abdb4 | 0.115 | R3 | code template, file-extension/size slot |
| 08142fe5 | 0.115 | R3 | HTML password label, `Re|Password` slot |
| fe863662 | 0.111 | R3 | code path template, `mask|soft` slot |
| 5471136e | 0.110 | R2 | academic prose, paragraph-opener locked on "The" |
| 7dbde4ff | 0.108 | R2 | code prose, `You can also return…` locked |
| e3da051e | 0.106 | R1- | `############` comment-line cycle |
| **05677c58** | 0.106 | **R3** | **ordinal-day enumeration** |
| b9eeb9e9 | 0.104 | R1- | `############` comment-line cycle |
| 6917c95f | 0.103 | R3 | C include `#include <…_v6.h>` |
| ed25bd71 | 0.096 | R3 | military service record, date/year rolling |
| 0a4614cd | 0.093 | R2/3 | Maven repo config, M/Nexus slot |
| 2982ff1c | 0.090 | R1 | `trump-trump-trump` cycle |
| **d58ffabc** | 0.090 | **R3** | **paper baselines list (numerical N rotation)** |
| f0a9edaa | 0.084 | R2 | Nintendo wiki paragraph cycle |
| **11b07bda** | 0.081 | **R3** | **counting "thing #N to note"** |
| d728e9bd | 0.075 | R2 | government-news, `The government has also announced…` |

(R1 = pinned, R2 = mode-locked, R3 = class-enumeration. R1- = R1 with tokenization-edge variability; R2/3 = ambiguous pending phase-aware analysis. Bold rows are the cleanest Regime-3 specimens — the measurement instruments.)

Pinned-regime examples (R1):

| oid (8) | shape sketch |
|---------|--------------|
| 48a8a855 | table dividers `---+---+---+` |
| 06e46d02 | URL path `/1/roles/1/` |
| 40380189, 9a2c70a8 | `[x] [x] [x]` checkbox cycle |
| 28657567 | `\string\string\string` JSON token |
| eec153e5 | pinned NCBI URL fragment |
| bc2d5bbc | `the _first_ thing to note` locked on " note" |

Full per-specimen tagging is mechanizable from `scripts/high_h_readout.py` output once the Regime-2/3 separator (chosen-token entropy across recurrences) is implemented; that is N1 below.

---

## Project implications

### Terminology

Survives intact: basin, attractor, trajectory, transient, perturbation, escape, interpretant, relational meaning, replication-with-error, self-conditioning, attending/attentional work, architectural attention.

Sharpens with empirical content: **crystal** — now a Regime-3 attractor, defined by a non-degenerate chosen-token distribution at one or more phase positions, with alt distributions readable as the model's prior over the slot's implicit class.

Retired as taxonomic categories (kept as predicate-firing record only): **candidate-basin** / **window_cap** as population axes.

New terms introduced this session:

- **pinned cycle** / **mode-locked structural attractor** / **class-enumeration attractor** — the three regimes (R1 / R2 / R3).
- **phase position** / **slot** / **scaffolding** — the per-cycle structure within an R2/R3 attractor.
- **shape metrics** — `onset`, `osc_amp`, `period`, `floor_H`, `floor_gap`, `gap_over_H`. Read-only computable over the persisted store.
- **measurement instrument** — Regime-3 framing: an attractor whose internal slot-prior is recoverable.
- **slot-readout** — the descriptive operation of reading high-H phase positions across recurrences for their alt distribution.

### Execution

- The cartography frame has nameable empirical content for the first time: the three-regime taxonomy and Regime-3-as-measurement-instrument.
- The literature survey from `realignment.md` is still wanted. The Regime-3 separator's claim of distinctness from existing decoding-literature framings needs verification, not assumption.
- The next data run reorients away from "basin v2 detection" toward seeded class-enumeration probing (N3 below).
- `brief.md`, `design-reqs*.md` — already held historical; their re-cast or retire is downstream of the re-founding decision.
- `ROADMAP.md` step "basin-v2" — superseded; a fresh forward sequence wants writing once the phase-aware analysis (N1) lands.
- `basins.md` v0.3 catalog — held historical; v0.4 awaits N1.

### Foundation document

`foundation.md` is frozen by default. The session's findings *strengthen* the foundation rather than challenge it: triadic semiotics, relational meaning, replication-with-error, and the crystal hypothesis all received empirical traction. A re-founding cycle in the strict sense is not required by the finding. A deliberate revision pass to fold in the three-regime taxonomy and the Regime-3 measurement-instrument framing is appropriate before next-cycle commitments lock in.

### Catalog and project-deliverable shape

The realignment doc named the catalog as "the project's primary deliverable shape" and held it at risk under re-founding. The session's finding suggests the catalog survives, but reshaped: per-attractor entries should carry regime + slot-class + period + shape-metrics, not (only) cycle-token-id tuples. Token-id tuples remain useful as basin identity at the substrate-trajectory level; regime tagging adds the cross-substrate taxonomic axis.

---

## Research implications and next moves

In rough priority order, with cost annotations.

### N1. Phase-aware chosen-token analysis (read-only, ~50 LOC)

For each STRUCTURED candidate, identify cycle period (autocorrelation already computed), partition the deep window into phase positions, compute chosen-token entropy across recurrences per phase. The phase with the highest chosen-entropy is the slot; its alt-token distribution is the prior readout.

Output: per-specimen regime tag (R1/R2/R3), slot phase index, chosen-token distribution at slot, alt-token distribution at slot. This produces the v0.4 catalog mechanically.

This is the cleanest single statistic for separating Regime 2 from Regime 3, and the prerequisite for everything downstream.

### N2. Alternate-path continuation experiment (engine work, modest)

Pick high-H positions in Regime-3 attractors. Use `Injection(position=k, chosen_id=alt_token_id)` plus runner KV-prefill to extend from the alt branch. Two questions:

- **Transient leverage.** Does perturbing in the early transient (positions 0–500) redirect the eventual floor regime? If the same seed reliably leads to the same Regime regardless of transient perturbation, the regime is a deep attractor. If transient perturbation flips Regime, the regime is shallow.
- **Cyclic leverage.** Does perturbing at a per-cycle high-H position break the cycle, transition it, or get reabsorbed? Re-absorption at the perturbation period is the strongest signature of Regime-3-as-real-attractor.

Cost: small new script (`scripts/alt_path_continuation.py`), a few hundred new trajectories of inference with KV-cache prefill. Existing infrastructure handles persistence and identity.

### N3. Seeded class-enumeration experiment (engine work + design)

Pick a class with concrete predictions (mid-20th-century novelists, programming languages, periodic table elements, philosophical concepts), seed accordingly, run to L_arch, read the high-H slots and their alt distributions. Hypothesis-driven complement to the descriptive readout of the existing 100 trajectories.

The methodology question from `realignment.md` ("hypothesis-driven vs organic") sharpens here: the existing 100 trajectories *are* the organic prior; this is the hypothesis-driven complement. Both are valid; this one is now well-posed because the operational target (a Regime-3 attractor whose slot reads out the seeded class's prior) is named.

Cost: small set of seeds, ~20–100 trajectories per seed × O(seeds), persistence reuses identity scheme.

### N4. Literature survey (still wanted, per realignment)

Specifically targeting:

- Has anyone in the decoding-quality / mech-interp / dynamical-systems / generative-model-cartography literature named the Regime-3 (slot-readout) class?
- What's the relationship between slot-readout and induction-head circuits in Pythia (Olsson et al. and follow-ups)?
- Is there work on perturbation responses in T=0 cycles?
- Is there prior work using LM degenerate-regime structure as a prior-readout instrument?

Parallel to N1/N2 since it's external research, not blocking.

### N5. Cycle-aware sampling (speculative, engine work)

Per-step T modulation tied to dynamics state — T proportional to recent osc_amp, or T spike at per-cycle high-H phase. Inverts the standard nucleus-sampling framing (instead of fixing T globally to fight degeneration, listen to the dynamics' own signal of where slack lives). Separate research thread; not blocking on Cycle 1.

---

## Repo state and merge path

Branch hierarchy at the time of writing:

- `main` at `6245a01` (persistence layer landed; v0.3 catalog frozen).
- `basin-v2` at `596141b`, off `main` — five commits: pre-design calibration probe, observation entry for calibration probe, full-depth extension script + position-window panels, probe reads full trajectory + entropy-onset, 2026-05-07 observation entry confirming depth-collapse. `realignment.md` is on this branch as untracked at the time the session began.
- `plots` (current branch), off `basin-v2` — uncommitted at the time of writing: `scripts/plot_trajectories.py`, `scripts/high_h_readout.py`, `data/plots/*.png` (4 figures), this `findings.md`, plus `matplotlib` added to `pyproject.toml`.

Merge-path question — open. Two shapes considered:

- **A. Land basin-v2 then plots as separate merges to main**, preserving commit-by-commit narrative. Risk: basin-v2's pre-realignment commit messages will read as outdated by the time main sees them; the calibration probe was framed as "v2 detector pre-design data" which the depth-collapse finding immediately retired. Mitigation: a final basin-v2 commit message or a wrapper-commit can frame the historical contour explicitly.
- **B. Squash basin-v2 + plots into one or two coherent commits on main**, framing the whole arc (calibration probe → depth-collapse → realignment doc → plots → consolidation) as one unit. Cleanest history; loses commit-by-commit detail but preserves it in `observations.md` entries and `realignment.md` / this document.

**Recommendation**: B-flavored. Specifically:
1. Commit current `plots` work on this branch (scripts + figures + this findings.md + pyproject.toml).
2. Decide whether `realignment.md` lands as part of basin-v2 (where it was authored) or as part of the consolidation commit on main.
3. Squash-or-merge basin-v2 onto main as historical record (the data, the observation entries, the scripts; possibly without the unused v2-detector design framing).
4. Squash-or-merge plots onto main as the substantive new contribution (figures, slot-readout, three-regime taxonomy, this document).
5. Defer the doc refactor (`brief.md`, `design-reqs*.md`, `ROADMAP.md` rewrite, `foundation.md` revision pass, basins.md v0.4 schema) until after N1 lands and the regime tagging is mechanized — then a single deliberate refactor pass on main consumes this `findings.md` and re-distributes its content across the appropriate documents, retiring `findings.md` itself.

Independent of merge path: the `realignment.md`-named two-step (literature survey, then re-founding decision on main) still wants to happen before the next data run commits to a frame. The session's finding makes the re-founding decision easier — the cartography frame has empirical content — but does not retire the survey question, which is about external positioning, not internal soundness.

---

*Genealogy: the foundation document, the realignment document, this findings document. Together they record a re-founding-cycle event in three stages — frame, question, answer — held legible across re-foundings.*
