# Peirce — Claude session anchor (top-level)

*Shapes the context loaded into every Claude session at this path. README.md is the human-facing entry point; this file is for Claude's working context. `MEMORY.md` (auto-loaded) is the per-topic memory index.*

*Last reviewed: `6b0b331` / 2026-05-09, post Cycle-2 cleanup pass (basins.py + C1 production-run scripts retired to `v0.1-final` tag, lit-review.md landed, design-reqs.md @-included). If HEAD has moved past this commit, skim the diff before assuming the picture encoded here is current.*

## Always loaded

@README.md
@foundation.md
@design-reqs.md

## Cycle 2 — forward sequence

The empirical question the cycle carries is **shape-of-collapse taxonomy**. The substrate (`data/peirce.db`: 100 fp16 trajectories × 2047 materialised steps; persistence layer and runner stable; KV-cache prefill working) is reusable read-only. `design-reqs.md` states what's given; this section states the open moves.

The moves below are roughly priority-ordered. Each is small in code (read-only descriptive scripts dominate); none assumes the next has landed.

1. **Phase-aware chosen-token analysis.** Read-only over the substrate. For each trajectory whose deep window has measurable cycle period, partition by phase position and compute chosen-token entropy across recurrences per phase. Phases with non-zero chosen-entropy are slots; their alt distributions are the local prior over each slot's class. Produces the first attractor catalog under the slot/scaffolding decomposition.

2. **Alternate-path continuation.** Engine work, modest. Pick high-H positions, use `Injection` + KV-prefill to extend trajectories from the alt branch. Two questions: does perturbing in the early transient redirect the eventual collapse (transient leverage)? does perturbing at a per-cycle high-H position break / transition / re-absorb (cyclic leverage)? Re-absorption at the perturbation period would be the strongest signature of a stable structured attractor. Argmax-of-non-chosen is the simplest branch-selection rule; the principled extension once first results are in is Gumbel-Top-k sampling-without-replacement (Kool 2019) at the perturbation position, giving K plausible alt-branches proportional to model probability rather than a single argmax pick — see lit-review.md addendum.

3. **Seeded class-enumeration probing.** Engine work + design. Pick a class with concrete priors (mid-20th-century novelists, programming languages, periodic-table elements), seed accordingly, run to L_arch, read the high-H slots' alt distributions. Hypothesis-driven complement to the descriptive readout from [BOS]-only trajectories.

4. **Literature survey** *(substantially closed; report at `lit-review.md`)*. Decoding-degeneration line (Holtzman 2019 onward) is uniformly avoidance-stance, with no within-cycle structural analysis. Markov-chain reframings (Zekri 2410.02724, Geng 2603.11228) and Wu 2502.15208 ("attractor cycle" at iterated-paraphrasing scope) are the closest dynamical-systems neighbours. The slot / scaffolding / slot-readout / class-enumeration-attractor neighbourhood appears genuinely unnamed in surveyed literature. Narrow follow-ups: full read of Wu 2502.15208 + Geng 2603.11228 (cite specifically once N1 lands); Holtzman 2019 re-read against the regime taxonomy — do their qualitative degenerate examples include class-enumeration specimens?

5. **Cycle-aware sampling.** Speculative; engine work. Per-step T modulation tied to dynamics state — T responsive to oscillation amplitude or spike at per-cycle high-H phases. Inverts the standard nucleus-sampling framing (instead of fixing T globally to fight degeneration, listen to the dynamics' own signal of where slack lives). Held until earlier moves stabilise the empirical surface.

This section rewrites here when a move closes or scope shifts. New parked threads land in `ideas.md` (which appears at root the first time the cycle has one).

## Other project docs

Read by reference, not @-included:
- `observations.md` — append-only commit-pinned empirical findings; loaded on demand when relevant to the work.
- `ideas.md` — append-only forward-looking threads. Appears at root when the current cycle has one; otherwise look in archive for prior-cycle threads if a revival becomes relevant. Restate in current-cycle voice rather than carrying forward retired vocabulary.
- `archive/` — prior-cycle record. Holds foundation v0.1, prior-cycle findings / brief / design-reqs / basins / ROADMAP / observations / ideas, plus `archive/deprecated-terms.md` (vocabulary explicitly retired in the v0.2 re-founding). Reproducibility for the prior cycle is via git tag `v0.1-final`.

## Working model

Daniel drives implementation in branches; main is for project direction, doc maintenance, and PR review. Sessions are sequential per branch; Daniel announces branch switches.

## Triggers

- **Branch-switch announced.** Re-read this CLAUDE.md and any path-specific CLAUDE.md for the new branch. Run `git log <other>..HEAD` both directions to surface divergence; raise rebase questions when substantive doc or spec changes have landed.
- **HEAD past Last-reviewed stamp on entry.** Skim commits since the stamp before substantive action; flag drift between the working picture encoded here and the current code/docs.
- **Wrapping a logical unit (commit, observation entry, design pivot).** Decide whether anything non-obvious surfaced that should land in memory.
- **Approaching /compact.** Triage in-flight state by scope. Project-level (cross-branch truth) → memory. Branch-level (commit progress, in-flight design state on a feature branch) → commit message, observation entry pinned to commit, or the branch's own CLAUDE.md if a handoff note is genuinely needed.
- **Hint of a re-founding event** — a finding that doesn't fit the foundation, or accumulating drift between foundation and active understanding. Surface deliberately rather than absorb silently. Re-foundings are normal and discrete; the discipline is to mark the cycle boundary, archive the prior cycle's working surface, tag the prior-cycle commit for reproducibility, and start the new cycle fresh.

## Memory

`MEMORY.md` indexes per-topic memory files and is the project's functional working state across sessions. Use for user / project / feedback / reference facts that should outlive a session. Don't duplicate CLAUDE.md content there. Memory is point-in-time observation; verify claims against current code before acting.

## Sub-path CLAUDE.md

Path-specific CLAUDE.md files are additive on top of this one. They typically @-include the path's README.md with a `(updated <commit>/<date>)` freshness annotation; noticing when the README has drifted from the pinned commit is part of the discipline.
