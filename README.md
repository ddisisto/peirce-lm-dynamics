# Peirce — LM Dynamics

*Empirical study of self-conditioning generative dynamics in language models.*

## Project documents

- [`foundation.md`](foundation.md) — frozen-by-default conceptual underpinning
- [`findings.md`](findings.md) — current consolidated working report (2026-05-07)
- [`realignment.md`](realignment.md) — re-founding-cycle document, companion to findings.md
- [`observations.md`](observations.md) — append-only log of empirical observations, each pinned to a commit hash and repro details
- [`basins.md`](basins.md) — basin catalog (v0.3 held historical pending v0.4)
- [`design-reqs.md`](design-reqs.md), [`brief.md`](brief.md) — revisable structural commitments / first-cycle inquiry shape; held historical pending the post-N1 doc redistribution

## Status

Cycle 1, mid-flight. Substrate built (100 trajectories × 2047 materialized steps in `data/peirce.db`); three-regime taxonomy of self-conditioning attractors at depth surfaced (R1 pinned / R2 mode-locked / R3 class-enumeration). See [`findings.md`](findings.md) for current working state and forward sequence.

## Quick start

Requires [`uv`](https://docs.astral.sh/uv/) and a CUDA-capable GPU.

```sh
uv sync
uv run python -m peirce
```

## Reproduction

*Each artifact is intended to be reproducible from a single command plus its manifest. To be filled in as scripts and artifacts land.*

## License

Apache-2.0. See [`LICENSE`](LICENSE).
