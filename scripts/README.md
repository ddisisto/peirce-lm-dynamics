# scripts/ — runs, renderers, smoke tests

Drivers over the `peirce/` library. Three kinds:

- **substrate-building runs** — populate the long-lived store at `data/peirce.db`
- **read-only renderers** — read the store, no model load, no inference; produce figures and stdout reports
- **smoke tests** — fast end-to-end checks of library invariants

All runs use `peirce.runner.observe(...)` rather than calling the engine directly. Re-running is idempotent: cached observations short-circuit, partial trajectories are extended in place via KV-cache prefill rather than regenerated.

## Substrate-building runs

- `full_depth_extension.py` — top-K from BOS × L_arch=2047 under predicates `[eos, window_cap]`, hard-cap T=0, one `Injection` per branch at position 0. From an empty store: builds the substrate from scratch. From a populated store (e.g. after C1's retired `broad_shallow` + `selection_bias` runs produced shallower observations of the same trajectories): cache-hits trajectory rows and prefills only the steps past their existing materialised depth. `FULL_DEPTH_TOP_K` env var overrides K (default 100). Forward-targeted for rename + docstring rewrite once the C2 substrate-construction story is locked; current docstring carries C1-historical motivation as record.

## Read-only renderers

- `plot_trajectories.py` — matplotlib renderings under `data/plots/`: `trajectories_aggregate.png`, `trajectories_shape.png`, `trajectories_outliers.png`, `trajectories_grid.png`. Per-trajectory shape metrics (`onset`, `floor_H`, `floor_gap`, `osc_amp`, `period`, `gap_over_H`) computed from the deep window `[1024, end)`. Filters observations to the C1 selection-bias predicate-set by string match against stored predicate-spec JSON; no live `basin_capture` code dependency.
- `high_h_readout.py` — top-N highest-entropy positions per trajectory in the deep window, with chosen / alt / context tokens. The descriptive half of the slot-readout operation. Same string-match filter as `plot_trajectories.py`.

## Smoke tests

- `smoke_engine.py` — short trajectories from BOS via top-k branching, dumps token-by-token records. Validates the engine without persistence.
- `smoke_kv_parity.py` — parity check: `observe_trajectory` (KV-cache + prefill) vs. a local full-context reference that re-encodes history every step. Pass criterion is exact token-id identity. Per-step scalar diffs reported as informational; at fp16 they sit at ~1e-2 (fp16 reduction-order noise), at fp32 they sit at ~1e-5.
- `smoke_store.py` — round-trip, idempotence, extension-via-prefill, short-budget shortcut, runner cache-hit, injection identity-distinction, query.

## Running

```sh
uv run python scripts/<name>.py
```

All store paths default to `<repo>/data/peirce.db` via `peirce.runner.default_store_path()`. Override with `PEIRCE_STORE=/path/to/other.db`.

## Retired (preserved at git tag `v0.1-final`)

The following C1-vintage scripts were retired in the cycle-2 cleanup pass and are recoverable from the `v0.1-final` tag:

- `broad_shallow.py` — top-K BOS × budget=64; the C1 substrate-builder under `[eos, basin_capture(K=4, max_period=16, cycle_window=64), budget_cap, window_cap]`.
- `selection_bias.py` — extended `broad_shallow`'s 100 trajectories to L_arch=2048 under a wider basin probe `[eos, basin_capture(K=4, max_period=32, cycle_window=256), window_cap]`.
- `representative_deep.py` — read-only renderer selecting six BOS-top-K branches and printing their L_arch observations with structural-cycle signatures via the retired `detect_tail_cycle`.
- `v2_calibration_probe.py` — basin-v2-line calibration probe, retired alongside the basin-v2 design direction.
