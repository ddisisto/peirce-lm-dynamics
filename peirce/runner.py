"""Cache-then-compute layer over the engine and store.

The runner is the seam between trajectory observation and persistence.
Consumers call `observe` with a trajectory spec and predicate set; the
runner checks the store, returns a cached observation if one exists,
extends a stored trajectory if its materialized depth falls short of
what the predicates need, or generates fresh otherwise.

Engine code stays store-unaware. Store code stays inference-unaware. The
runner makes them cooperate.
"""
from __future__ import annotations

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
    trajectory_hash_from_parts,
    write_observation,
)


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
