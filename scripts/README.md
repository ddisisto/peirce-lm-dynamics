# scripts/ — runs and smoke tests

Drivers over the `peirce/` library. Two kinds:

- **runs** — populate the long-lived store at `data/peirce.db` and produce stdout reports
- **smoke tests** — fast end-to-end checks of library invariants

All runs use `peirce.runner.observe(...)` rather than calling the engine directly. Re-running is idempotent: cached observations short-circuit, partial trajectories are extended in place via KV-cache prefill rather than regenerated.

## Runs

- `broad_shallow.py` — top-K from BOS × budget=64, hard-cap T=0, one Injection per branch at position 0. Fresh on first run; cache-hits on re-run. `BROAD_SHALLOW_TOP_K` env var overrides K (default 100). Predicates: eos, basin_capture (max_period=16, cycle_window=64), budget_cap, window_cap.
- `selection_bias.py` — extends broad_shallow's 100 trajectories to L_arch=2048 under a wider basin probe (max_period=32, cycle_window=256, no budget_cap). Trajectory rows cache-hit; observations are fresh because the predicate set differs. Engine prefills from broad_shallow's 64 steps and continues. `SELECTION_BIAS_TOP_K` env var overrides K. Per-trajectory wall time printed inline.
- `representative_deep.py` — read-only renderer over the store. No model load, no inference. Selects six BOS-top-K branches by chosen_id (rank-stable; created_at is second-precision and not stable as an ordering key) and prints their L_arch observation: terminal event, length, basin signature when captured, head/tail entropy and log-prob windows.

## Smoke tests

- `smoke_engine.py` — short trajectories from BOS via top-k branching, dumps token-by-token records. Validates the engine without persistence.
- `smoke_kv_parity.py` — parity check: `observe_trajectory` (KV-cache + prefill) vs. a local full-context reference that re-encodes history every step. Pass criterion is exact token-id identity. Per-step scalar diffs reported as informational; at fp16 they sit at ~1e-2 (fp16 reduction-order noise), at fp32 they sit at ~1e-5.
- `smoke_store.py` — round-trip, idempotence, extension-via-prefill, short-budget shortcut, runner cache-hit, injection identity-distinction, query.

## Running

```sh
uv run python scripts/<name>.py
```

All store paths default to `<repo>/data/peirce.db` via `peirce.runner.default_store_path()`. Override with `PEIRCE_STORE=/path/to/other.db`.

## Selection criteria caveat

`representative_deep.py` selects by chosen_id, not by rank. Reason: `trajectories.created_at` is second-precision in SQLite, and broad_shallow inserts ~3 trajectories per second, so insertion-order ranks tie-break unstably. Future scripts that want a "rank N from BOS" reference either (a) load the model briefly and recompute top-K from the BOS distribution, or (b) hardcode chosen_ids derived from the tokenizer.
