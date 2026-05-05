# Peirce — Claude session anchor (top-level)

*Shapes the context loaded into every Claude session at this path. README.md is the human-facing entry point; this file is for Claude's working context. `MEMORY.md` (auto-loaded) is the per-topic memory index.*

*Last reviewed: `6245a01` / 2026-05-05. If HEAD has moved since the stamp, skim the diff before assuming the picture encoded here is current.*

## Always loaded

@README.md
@foundation.md
@ROADMAP.md

Other project docs are read by reference, not @-included:
- `brief.md`, `design-reqs.md`, `design-reqs-records.md`, `design-reqs-steering.md` — subject to drift; held out of the auto-loaded set until the design-reqs refactor (per ROADMAP) settles them.
- `observations.md`, `basins.md`, `ideas.md` — grow over time; loaded on demand when relevant to the work.

## Working model

Daniel drives implementation in branches; main is for project direction, doc maintenance, and PR review. Sessions are sequential per branch; Daniel announces branch switches.

## Triggers

- **Branch-switch announced.** Re-read this CLAUDE.md and any path-specific CLAUDE.md for the new branch. Run `git log <other>..HEAD` both directions to surface divergence; raise rebase questions when substantive doc or spec changes have landed.
- **HEAD past Last-reviewed stamp on entry.** Skim commits since the stamp before substantive action; flag drift between the working picture encoded here and the current code/docs.
- **Wrapping a logical unit (commit, observation entry, design pivot).** Decide whether anything non-obvious surfaced that should land in memory.
- **Approaching /compact.** Triage in-flight state by scope. Project-level (cross-branch truth) → memory. Branch-level (commit progress, in-flight design state on a feature branch) → commit message, observation entry pinned to commit, or the branch's own CLAUDE.md if a handoff note is genuinely needed.

## Memory

`MEMORY.md` indexes per-topic memory files and is the project's functional working state across sessions. Use for user / project / feedback / reference facts that should outlive a session. Don't duplicate CLAUDE.md content there. Memory is point-in-time observation; verify claims against current code before acting.

## Sub-path CLAUDE.md

Path-specific CLAUDE.md files are additive on top of this one. They typically @-include the path's README.md with a `(updated <commit>/<date>)` freshness annotation; noticing when the README has drifted from the pinned commit is part of the discipline.
