# Peirce — LM Dynamics

*Empirical study of self-conditioning generative dynamics in language models.*

## Project documents

- [`foundation.md`](foundation.md) — frozen-by-default conceptual underpinning
- [`design-reqs.md`](design-reqs.md) — revisable structural commitments
- [`brief.md`](brief.md) — shape of inquiry across cycles and the first cycle's concrete moves
- [`observations.md`](observations.md) — append-only log of empirical observations, each pinned to a commit hash and repro details

## Status

Phase 0 — substrate selection and harness setup. No artifacts produced yet.

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
