# Peirce — LM Dynamics

*Empirical study of self-conditioning generative dynamics in language models.*

## Project documents

- [`foundation.md`](foundation.md) — frozen-by-default conceptual underpinning (v0.2)
- [`observations.md`](observations.md) — append-only log of empirical observations, each pinned to a commit hash and repro details
- [`archive/`](archive/) — prior-cycle working surface (foundation v0.1, design-reqs, brief, basins catalog, ROADMAP, findings, realignment, observations, ideas), plus a deprecated-terms checklist. Reproducibility for prior-cycle observations resolves via the [`v0.1-final`](../../releases/tag/v0.1-final) tag.

## Status

Cycle 2 commencing. Cycle 1 (tagged [`v0.1-final`](../../releases/tag/v0.1-final)) produced a stable substrate — 100 fp16 trajectories × 2047 materialised steps in `data/peirce.db`, content-addressed persistence, runner with KV-cache prefill — and surfaced **shape-of-collapse taxonomy** as the empirical question Cycle 2 carries forward.

The primary object of study is *context collapse*: the per-trajectory phenomenon of entropy collapsing to a low floor under T=0 self-conditioning. The project takes context collapse as a phenomenon to characterise rather than a problem to suppress, and looks at the *shape* of how the collapse arrives, the structure carried within once it has, and the response of these structures to perturbation. See [`foundation.md`](foundation.md) for the full framing.

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
