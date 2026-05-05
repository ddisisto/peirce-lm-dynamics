"""Trajectory observation under hard-cap T=0 inference.

The unit of work is `observe_trajectory`: extend a trajectory under a
predicate set until a predicate fires, returning an Observation. If the
trajectory has no materialized steps yet, this is fresh generation. If
it has existing steps, the engine prefills the KV cache from those steps
in a single forward pass and continues stepping from there.

This unifies fresh generation and trajectory extension under one path —
extending a stored 100-step trajectory to depth 200 costs one prefill of
size 100 plus 100 incremental steps, which is meaningfully cheaper than
regenerating 200 steps from scratch (the prefill parallelizes across
positions, while incremental stepping does not).

Predicates are checked against the existing materialized steps before
stepping. A predicate firing within the existing prefix terminates the
observation without any inference — useful when a smaller-budget
observation is requested against a trajectory that already has more
steps materialized than the budget would allow.

Injections are intent-level interventions, recorded on the trajectory
object. At each step's position, if the position has an injection, the
chosen token is the injection's token; otherwise it is the natural
argmax. The recorded step still measures the natural distribution
(log_prob of chosen, alt fields point to the natural argmax when chosen
diverges from it). HF's GPTNeoX-family infers position ids from the
cache length, so explicit position_ids are unnecessary at hard-cap T=0.
"""
from __future__ import annotations

from typing import Sequence

import torch
import transformers
from transformers import PreTrainedModel, PreTrainedTokenizerBase

from .predicates import Predicate
from .records import (
    InferenceStrategy,
    Injection,
    Observation,
    PredicateSpec,
    StackIdentity,
    StepRecord,
    Trajectory,
)


def _capture_stack(model: PreTrainedModel, model_revision: str | None) -> StackIdentity:
    """Snapshot the producing-system identity at trajectory creation."""
    model_id = getattr(model, "name_or_path", None) or getattr(
        model.config, "_name_or_path", None
    )
    return StackIdentity(
        model_id=model_id,
        model_revision=model_revision,
        dtype=str(model.dtype),
        device=str(next(model.parameters()).device),
        torch_version=torch.__version__,
        transformers_version=transformers.__version__,
        deterministic_flags={
            "torch.use_deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
            "torch.backends.cudnn.deterministic": torch.backends.cudnn.deterministic,
            "torch.backends.cudnn.benchmark": torch.backends.cudnn.benchmark,
            "torch.float32_matmul_precision": torch.get_float32_matmul_precision(),
        },
    )


def _spec_for(pred: Predicate) -> PredicateSpec:
    return PredicateSpec(
        name=getattr(pred, "name", "<unnamed>"),
        params=dict(getattr(pred, "params", {})),
    )


def fresh_trajectory(
    model: PreTrainedModel,
    initial_ids: Sequence[int],
    injections: Sequence[Injection] = (),
    model_revision: str | None = None,
) -> Trajectory:
    """Build an empty Trajectory with stack identity captured from the model."""
    return Trajectory(
        stack=_capture_stack(model, model_revision),
        initial_ids=list(initial_ids),
        injections=tuple(injections),
    )


@torch.no_grad()
def observe_trajectory(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizerBase,
    trajectory: Trajectory,
    predicates: Sequence[Predicate],
    inference_strategy: InferenceStrategy | None = None,
) -> Observation:
    """Extend a trajectory under predicates, return the resulting Observation.

    Mutates `trajectory.steps` in place to append any newly-generated steps.
    Predicates fired within the existing materialized prefix terminate the
    observation without running the model.
    """
    if inference_strategy is None:
        inference_strategy = InferenceStrategy(name="hard_cap_t0", params={})

    pred_specs = tuple(_spec_for(p) for p in predicates)

    full_history = list(trajectory.initial_ids)
    n_existing = len(trajectory.steps)
    terminal_event: str | None = None
    observed_length = 0

    for i, s in enumerate(trajectory.steps):
        full_history.append(s.token_id)
        observed_length = i + 1
        steps_view = trajectory.steps[:observed_length]
        for predicate in predicates:
            tag = predicate(full_history, steps_view, observed_length)
            if tag is not None:
                terminal_event = tag
                break
        if terminal_event is not None:
            break

    if terminal_event is not None:
        return Observation(
            trajectory=trajectory,
            predicates=pred_specs,
            inference_strategy=inference_strategy,
            terminal_event=terminal_event,
            observed_length=observed_length,
        )

    device = next(model.parameters()).device

    input_ids = torch.tensor([full_history], device=device)
    outputs = model(input_ids, use_cache=True)
    past_kv = outputs.past_key_values
    logits = outputs.logits[0, -1, :]

    injection_at = {inj.position: inj.chosen_id for inj in trajectory.injections}

    while terminal_event is None:
        log_probs = torch.log_softmax(logits, dim=-1)
        probs = log_probs.exp()
        entropy = -(probs * log_probs).sum().item()
        top2 = torch.topk(probs, 2)
        top2_ids = top2.indices.tolist()
        top2_probs = top2.values.tolist()
        logit_gap = log_probs[top2_ids[0]].item() - log_probs[top2_ids[1]].item()

        natural_argmax_id = top2_ids[0]
        position = len(trajectory.steps)
        chosen_id = injection_at.get(position, natural_argmax_id)

        chosen_log_prob = log_probs[chosen_id].item()
        chosen_token = tokenizer.decode([chosen_id])

        if natural_argmax_id != chosen_id:
            alt_id, alt_prob = natural_argmax_id, top2_probs[0]
        else:
            alt_id, alt_prob = top2_ids[1], top2_probs[1]
        alt_token = tokenizer.decode([alt_id])

        trajectory.steps.append(StepRecord(
            token_id=chosen_id,
            token=chosen_token,
            log_prob=chosen_log_prob,
            entropy=entropy,
            alt_token_id=alt_id,
            alt_token=alt_token,
            alt_prob=alt_prob,
            logit_gap=logit_gap,
        ))
        full_history.append(chosen_id)
        observed_length = len(trajectory.steps)

        steps_view = trajectory.steps[:observed_length]
        for predicate in predicates:
            tag = predicate(full_history, steps_view, observed_length)
            if tag is not None:
                terminal_event = tag
                break

        if terminal_event is None:
            input_ids = torch.tensor([[chosen_id]], device=device)
            outputs = model(input_ids, past_key_values=past_kv, use_cache=True)
            past_kv = outputs.past_key_values
            logits = outputs.logits[0, -1, :]

    return Observation(
        trajectory=trajectory,
        predicates=pred_specs,
        inference_strategy=inference_strategy,
        terminal_event=terminal_event,
        observed_length=observed_length,
    )
