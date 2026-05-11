# scripts/ — runs, renderers, smoke tests

Drivers over the `peirce/` library. Three kinds:

- **substrate-building runs** — populate the long-lived store at `data/peirce.db`
- **read-only renderers** — read the store, no model load, no inference; produce figures and stdout reports
- **smoke tests** — fast end-to-end checks of library invariants

All runs use `peirce.runner.observe(...)` rather than calling the engine directly. Re-running is idempotent: cached observations short-circuit, partial trajectories are extended in place via KV-cache prefill rather than regenerated.

## Substrate-building runs

- `full_depth_extension.py` — top-K from BOS × L_arch=2047 under predicates `[eos, window_cap]`, hard-cap T=0, one `Injection` per branch at position 0. From an empty store: builds the substrate from scratch. From a populated store (e.g. after C1's retired `broad_shallow` + `selection_bias` runs produced shallower observations of the same trajectories): cache-hits trajectory rows and prefills only the steps past their existing materialised depth. `FULL_DEPTH_TOP_K` env var overrides K (default 100). Forward-targeted for rename + docstring rewrite once the C2 substrate-construction story is locked; current docstring carries C1-historical motivation as record.

## Read-only renderers

All read-only renderers iterate the `trajectories` table directly (one row per `trajectory_id`, distinct from per-`observation_id`). Trajectory steps are shared across observations in `trajectory_steps`, so the underlying substrate is the same regardless of which observation row's metadata was used; iterating trajectories drops a vestigial selection-bias-observation filter from C1 and converges the renderers on `trajectory_id[:8]` as the persistent identifier in stdout.

- `shape_catalog.py` — the C2 consolidated descriptive catalog under v0.2 vocabulary. Per-trajectory rows grouped by tag (SLOTTED-CLASS / -COUNTER-INT / -COUNTER-LETTER / -MIXED / SCAFFOLD / NOPERIOD), per-slot chosen + alt distributions with delta-evidence for the counter-vs-class heuristic, position-resolved `logit_gap` and `gap_over_H` readouts. Aggregate sections: counts by tag, top-K candidate positions by lowest `gap_over_H` (principled N2 candidates) and highest H (baseline). Reports `peaks=` per row so period-convention choices are auditable.
- `phase_aware_chosen.py` — N1 first-light renderer; partitions deep window by phase (under the `peirce.shape.dominant_period` convention) and prints chosen + alt distributions per slot. Functionally subsumed by `shape_catalog.py` for canonical use; preserved as the leaner standalone reading.
- `noperiod_audit.py` — diagnostic readout of the catalog's NOPERIOD bucket. Per specimen, shows peaks under default + relaxed `PEAK_MIN` and widened `LAG_MAX`, plus top raw-acf values (no strict-local-max filter), to distinguish honest no-period (monotonic acf decay) from weak-sub-threshold-structure (bimodal H with weak quasi-periodic peaks). Read-only over the substrate; no model load.
- `plot_trajectories.py` — matplotlib renderings under `data/plots/`: `trajectories_aggregate.png`, `trajectories_shape.png`, `trajectories_outliers.png`, `trajectories_grid.png`. Per-trajectory shape metrics (`onset`, `floor_H`, `floor_gap`, `osc_amp`, `period`, `gap_over_H`) computed from the deep window `[1024, end)`.
- `high_h_readout.py` — top-N highest-entropy positions per trajectory in the deep window, with chosen / alt / context tokens. The descriptive half of the slot-readout operation.

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

## Aspirational — C2 branching surface

The C2 branching protocol (`design-reqs.md`) extends the script set:

- **Branch runs.** Per-batch scripts driving `runner.branch_observe`. First batch is ~10 branches across regime tags per the protocol; the run reads candidate positions from the C2 catalog's principled (lowest `gap_over_H`) and baseline (highest deep-window H) lists, builds branch runs using each candidate's persisted `alt_token_id` (first-batch argmax-of-non-chosen rule), persists the resulting trajectories. Cache-hits on re-run via the existing observation-identity seam.
- **Branch comparison renderer.** A read-side renderer that puts parent and branch on common axes — token-level divergence, H-trace divergence, position-resolved `logit_gap` and `gap_over_H`. Named here; design deferred until first-batch results inform the relevant comparisons.
- **Position-N>0 injection smoke-test.** Pre-flight before first-batch runs. Extends `smoke_engine` to exercise mid-trajectory injections (substrate-construction smoke only covers position-0). Position-N injection rides the existing `Injection` schema atom unchanged; the smoke confirms engine behaviour matches the contract.
