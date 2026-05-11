"""Cache-then-compute layer over the engine and store.

The runner is the seam between trajectory observation and persistence.
Consumers call `observe` with a trajectory spec and predicate set; the
runner checks the store, returns a cached observation if one exists,
extends a stored trajectory if its materialized depth falls short of
what the predicates need, or generates fresh otherwise.

Engine code stays store-unaware. Store code stays inference-unaware. The
runner makes them cooperate.

`default_store_path()` resolves the canonical long-lived store location
(repo-root `data/peirce.db`, or `$PEIRCE_STORE` if set), creating the
parent directory if needed. Scripts that just want "the store" call
this and pass the result to `open_store`.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence

from transformers import PreTrainedModel, PreTrainedTokenizerBase

from .engine import _capture_stack, _spec_for, fresh_trajectory, observe_trajectory
from .predicates import Predicate
from .records import (
    InferenceStrategy,
    Injection,
    Observation,
)
from .store import (
    find_observation,
    find_trajectory,
    read_trajectory,
    trajectory_hash_from_parts,
    write_observation,
)


def default_store_path() -> Path:
    """Canonical store path: $PEIRCE_STORE if set, else <repo>/data/peirce.db.

    Creates the parent directory if it does not exist. Repo root is
    inferred as the parent of the peirce package directory.
    """
    env = os.environ.get("PEIRCE_STORE")
    if env:
        path = Path(env)
    else:
        repo_root = Path(__file__).resolve().parent.parent
        path = repo_root / "data" / "peirce.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def observe(
    store,
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizerBase,
    *,
    initial_ids: Sequence[int],
    predicates: Sequence[Predicate],
    injections: Sequence[Injection] = (),
    inference_strategy: InferenceStrategy | None = None,
    model_revision: str | None = None,
) -> Observation:
    """Get-or-compute an observation, persisting any new work.

    Resolution order:
      1. Compute trajectory_id from (stack, initial_ids, injections).
      2. If an observation with matching predicates and inference_strategy
         exists, return it.
      3. If the trajectory exists in the store, load its materialized steps
         and call observe_trajectory — extension or no-op as needed.
      4. If the trajectory does not exist, build a fresh one and call
         observe_trajectory — full generation.
      5. Persist the resulting observation (new trajectory steps, if any,
         appended; observation row inserted).
    """
    if inference_strategy is None:
        inference_strategy = InferenceStrategy(name="hard_cap_t0", params={})

    stack = _capture_stack(model, model_revision)
    initial_list = list(initial_ids)
    injection_tuple = tuple(injections)
    trajectory_id = trajectory_hash_from_parts(stack, initial_list, injection_tuple)

    pred_specs = tuple(_spec_for(p) for p in predicates)
    cached = find_observation(store, trajectory_id, pred_specs, inference_strategy)
    if cached is not None:
        return cached

    stored = find_trajectory(
        store,
        fresh_trajectory(model, initial_list, injection_tuple, model_revision),
    )
    trajectory = stored if stored is not None else fresh_trajectory(
        model, initial_list, injection_tuple, model_revision
    )

    obs = observe_trajectory(
        model, tokenizer, trajectory, predicates,
        inference_strategy=inference_strategy,
    )
    write_observation(store, obs)
    return obs


def branch_observe(
    store,
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizerBase,
    *,
    parent_trajectory_id: str,
    branch_position: int,
    alt_token_id: int,
    predicates: Sequence[Predicate],
    inference_strategy: InferenceStrategy | None = None,
    model_revision: str | None = None,
) -> Observation:
    """C2 branching protocol primitive: branch a parent at branch_position with alt_token_id.

    Reads the parent trajectory from the store, appends
    `Injection(branch_position, alt_token_id)` to its injection tuple, and
    delegates to `observe`. The branch trajectory's `trajectory_id` is fresh
    by hash construction over the augmented injection tuple; the path through
    `observe → engine → store` is unchanged. Branch trajectories cache-hit on
    re-run via the standard observation-identity seam.

    `branch_position` must be >= 1. Position 0 is the initial-condition
    selection role for the `Injection` schema atom (substrate construction);
    `branch_observe` is the mid-trajectory perturbation primitive only.
    To create an alternate initial condition, call `observe` directly with
    the desired position-0 injection.

    `branch_position` must not collide with an existing injection on the
    parent at the same position. The engine resolves duplicate-position
    injections via dict semantics (last write wins), which would silently
    overwrite the parent's injection — rejected here explicitly.

    Raises KeyError if `parent_trajectory_id` is not in the store.
    Raises ValueError on the validation conditions above.
    """
    if branch_position < 1:
        raise ValueError(
            f"branch_position must be >= 1 (got {branch_position}); "
            "position 0 is initial-condition selection — call observe() directly"
        )
    parent = read_trajectory(store, parent_trajectory_id)
    existing_positions = {inj.position for inj in parent.injections}
    if branch_position in existing_positions:
        raise ValueError(
            f"branch_position {branch_position} collides with an existing "
            f"injection on parent {parent_trajectory_id} at the same position"
        )
    new_injections = (
        *parent.injections,
        Injection(position=branch_position, chosen_id=alt_token_id),
    )
    return observe(
        store, model, tokenizer,
        initial_ids=parent.initial_ids,
        predicates=predicates,
        injections=new_injections,
        inference_strategy=inference_strategy,
        model_revision=model_revision,
    )
