# scripts/ — Claude session anchor

*Additive on top of the top-level `CLAUDE.md`.*

@README.md *(updated 2026-05-17 — regime-tag audit landed; resolver module is next, planning + findings in `notes/regime-tag-consolidation.md`)*

## Standards within this path

- **Use `runner.observe`, not `engine.observe_trajectory` directly.** Scripts that bypass the runner skip cache-hit short-circuits, lose persistence, and re-do work that's already on disk. Engine direct-call is appropriate only in smoke tests that explicitly test engine behavior.
- **Reuse existing trajectories where the science permits.** A new run with a different predicate set against the same `(stack, initial_ids, injections)` tuple cache-hits on the trajectory and extends from its materialized depth — no need to start from scratch. selection_bias's reuse of broad_shallow's 100 is the canonical example.
- **Default store path for first-class runs.** Use `default_store_path()` so all scripts converge on `data/peirce.db`. One-off probes that shouldn't pollute the long-lived store can write to a tempfile or a `$PEIRCE_STORE` override.
- **Smoke tests stay self-contained.** They open their own (usually in-memory or tempfile) store, exercise a specific contract, and either pass loudly or fail with a diagnostic. They do not write to the long-lived `data/peirce.db`.
- **Scripts are reproducible from a single command + the store.** No interactive prompts, no hidden state. Env-var overrides (e.g. `BROAD_SHALLOW_TOP_K`) for smoke variants of the same script are fine; gating behavior on undocumented file presence is not.
- **Read-only renderers don't load the model.** If a script's job is to present what's in the store, tokenizer + sqlite is enough. Loading the model just to derive a rank-K mapping is a smell — prefer chosen_id-based selection or a model-derived constant cached at script time.

## When something here changes

If a script's role shifts (e.g. selection_bias absorbing what representative_deep used to do), update the README *and* the script docstring. Drift between the two is a signal that the path's role hasn't been thought through end-to-end.

The freshness stamp on the `@README.md` line above pins this CLAUDE.md to a specific README revision.
