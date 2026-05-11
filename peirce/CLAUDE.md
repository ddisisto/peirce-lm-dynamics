# peirce/ — Claude session anchor

*Additive on top of the top-level `CLAUDE.md`.*

@README.md *(updated 2026-05-11 — C2 branching protocol aspirational surface)*

## Standards within this path

- **Engine stays store-unaware. Store stays inference-unaware. Runner mediates.** New persistence concerns belong in `store.py` or `runner.py`. New inference concerns belong in `engine.py`. If a change wants to cross the seam, surface it before refactoring.
- **Manifest-hash identity is the contract.** Anything that participates in trajectory or observation identity (stack fields, initial_ids, injections, predicate specs, inference strategy) must serialize to canonical JSON the same way `_canonical_json` does. Adding a new identity-bearing field means updating both the dataclass and the hash construction; never one without the other.
- **Write-once on observation_id.** Re-running a script is idempotent. If a feature wants mutability — overwriting an observation's terminal_event, for instance — the design choice is whether to write a new observation row or change the schema; never to silently re-write.
- **Trajectories are extensible; observations are frozen.** Mutate `trajectory.steps` in place when extending; build a fresh `Observation` for each run. The split exists so multiple observations share trajectory rows.
- **Stack identity captures the producing system, not the experimenter's intent.** Model, dtype, device, library versions, deterministic flags. Predicate set and inference strategy belong on the observation side.

## When something here changes

If a change touches the runner / store / engine seam, the README's "How they fit together" diagram is the place to sanity-check that the seam is still clean. If the diagram needs updating, update it; if a change wants to violate it, escalate before merging.

The freshness stamp on the `@README.md` line above pins this CLAUDE.md to a specific README revision. When HEAD has moved past the stamp and substantive package changes have landed, re-read the README and update the stamp (or the README) accordingly.
