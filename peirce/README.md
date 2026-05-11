# peirce/ — package

The library code. Scripts in `../scripts/` drive runs against this surface.

## Modules

- `records.py` — dataclasses. `Trajectory` (intrinsic: stack + initial_ids + injections + materialized steps), `Observation` (experimenter's run: trajectory + predicate set + inference strategy + terminal event + observed_length). `StepRecord`, `StackIdentity`, `Injection`, `PredicateSpec`, `InferenceStrategy`. Identity: `trajectory_id = hash(stack, initial_ids, injections)`, `observation_id = hash(trajectory_id, predicates, inference_strategy)`.
- `shape.py` — pure functions over numpy arrays of per-step quantities; no engine, no store, no model. `entropy_onset` (collapse-speed scalar), `acf_peaks` (autocorrelation peak list — the underlying period-structure measurement), `dominant_period` (single-int convention over `acf_peaks`; smallest in-list divisor of the strongest peak). Convention constants `DEEP_START = 1024`, `LAG_MIN/LAG_MAX/PEAK_MIN`, `ONSET_THRESHOLD/ONSET_SMOOTHING`. Catalog renderers and shape-axis plots compute over the deep window using these.
- `engine.py` — `observe_trajectory` extends a Trajectory under predicates, returning an Observation. KV-cache prefill from existing materialized steps + incremental stepping for any additional steps. `fresh_trajectory` builds an empty Trajectory with stack identity captured from a model. Predicates checked against the existing prefix first (zero-inference shortcut when a shorter budget is requested against an already-deeper trajectory).
- `predicates.py` — terminal-event predicates as `(history, records, n_steps) -> tag | None` callables with `.name` and `.params` attached. Factories: `eos_predicate`, `budget_cap_predicate`, `window_cap_predicate`.
- `store.py` — SQLite store. Three tables: `trajectories`, `trajectory_steps`, `observations`. Manifest-hash identity, write-once on observation_id, trajectory rows upserted with new steps appended. `open_store`, `write_observation`, `read_observation`, `read_trajectory`, `find_trajectory`, `find_observation`, `query_observations`.
- `runner.py` — cache-then-compute seam. `observe(store, model, tokenizer, *, initial_ids, predicates, injections=())` resolves: (1) matching observation in store → return cached, (2) trajectory in store → load steps, extend or no-op via engine, (3) else fresh generation. Persists any new work. `branch_observe(store, model, tokenizer, *, parent_trajectory_id, branch_position, alt_token_id, predicates)` is the C2 branching primitive — reads parent, appends `Injection(branch_position, alt_token_id)` to its injection tuple, delegates to `observe`. Guards `branch_position >= 1` (position-0 is initial-condition selection, not mid-trajectory perturbation) and collision with existing parent injections. `default_store_path()` resolves `<repo>/data/peirce.db` (or `$PEIRCE_STORE`).

## How they fit together

```
script ──► runner.observe ──► store.find_observation ──► (cache hit, return)
                          │
                          └─► store.find_trajectory + engine.observe_trajectory
                                       │                       │
                                       │                       └─► extends trajectory
                                       │                            in place; predicates
                                       │                            terminate the observation
                                       │
                                       └─► store.write_observation persists new work
```

Engine code is store-unaware. Store code is inference-unaware. The runner mediates.

## Identity

Two hashes, both blake2b-16 over canonical JSON.

- Trajectory identity = stack identity (model, dtype, device, library versions, deterministic flags) + initial_ids + injections. Same trajectory across re-runs ⇒ same id ⇒ shared row. Cross-stack runs (different dtype, different device) yield distinct trajectories — the comparison path stays a separate concern.
- Observation identity = trajectory_id + predicate specs + inference strategy. A budget=64 observation and a budget=2048 observation of the same trajectory share trajectory_steps but are distinct observation rows.

Consequence: re-running a script is idempotent. Trajectories are extended (KV prefill from existing steps + incremental stepping for the rest), not regenerated.

## Inference

Currently always `name="hard_cap_t0"`. T>0 sampling and sliding-window variants will populate the `params` dict on `InferenceStrategy` and add per-step placement-event records on the observation side (sampling deviations) rather than the trajectory side (which carries intent only — initial_ids + injections).

## Aspirational — C2 branching surface

`branch_observe` is landed (see the runner module bullet above). One operation remains aspirational, pending the second-batch alt-selection rule:

- **`step_distribution(store, model, tokenizer, trajectory_id, position, *, top_k=...)`** — recovers the model's distribution at a step of an existing trajectory. Needed for second-batch Gumbel-Top-k alt-selection, since persisted `StepRecord`s carry chosen + alt + entropy + logit_gap but not the full top-K. Single forward pass through the prefix via KV-prefill; result is returned, not persisted. (A future schema extension could persist top-K around branch points if analysis demands it; deferred until empirical questions warrant it.)

The inference strategy at branch-time remains `hard_cap_t0`. Alt-token selection — whether argmax-of-non-chosen (read from persisted `StepRecord.alt_token_id`) or Gumbel-Top-k (sampled from `step_distribution` output) — is a script-side decision, not an inference-strategy parameter; at branch-time the chosen alt is just another `Injection`.
