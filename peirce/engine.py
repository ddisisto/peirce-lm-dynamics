"""Trajectory generation under hard-cap T=0 inference.

Generates a trajectory by appending one argmax token at a time to the running
context, recording per-step thin records, until a terminal event fires. The
first step may be overridden to enable top-k-from-BOS branching: at step 0,
a forced token is chosen instead of the argmax, but its position in the
distribution is recorded normally (log-probability, entropy, top-2). The
override is also recorded as an injection entry in the trajectory's
rank-event log.

Uses the HF KV cache (`past_key_values`) so each subsequent step feeds only
the newly-chosen token to the model rather than re-running the full context.
This converts per-trajectory work from O(L^2) to O(L) token-forward-passes.
HF's GPTNeoX-family infers position ids from the cache length, so explicit
position_ids are unnecessary at hard-cap T=0.

The returned Trajectory is the design-reqs-records "observation packet":
stack identity, initial condition, predicate set, inference strategy, thin
records, rank-event log, and terminal event. Aggregate-certainty caching
and a Window class are downstream concerns and not yet captured.
"""
from __future__ import annotations

from typing import Sequence

import torch
import transformers
from transformers import PreTrainedModel, PreTrainedTokenizerBase

from .predicates import Predicate
from .records import (
    InferenceStrategy,
    PredicateSpec,
    RankEvent,
    StackIdentity,
    StepRecord,
    Trajectory,
)


def _capture_stack(model: PreTrainedModel, model_revision: str | None) -> StackIdentity:
    """Snapshot the producing-system identity at trajectory generation time."""
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


@torch.no_grad()
def generate_trajectory(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizerBase,
    initial_ids: Sequence[int],
    predicates: Sequence[Predicate],
    first_step_override: int | None = None,
    inference_strategy: InferenceStrategy | None = None,
    model_revision: str | None = None,
) -> Trajectory:
    if inference_strategy is None:
        inference_strategy = InferenceStrategy(name="hard_cap_t0", params={})

    device = next(model.parameters()).device
    history: list[int] = list(initial_ids)
    steps: list[StepRecord] = []
    rank_events: list[RankEvent] = []
    terminal_event: str | None = None

    input_ids = torch.tensor([history], device=device)
    past_kv = None

    while terminal_event is None:
        outputs = model(input_ids, past_key_values=past_kv, use_cache=True)
        past_kv = outputs.past_key_values
        logits = outputs.logits[0, -1, :]
        log_probs = torch.log_softmax(logits, dim=-1)
        probs = log_probs.exp()
        entropy = -(probs * log_probs).sum().item()

        top2 = torch.topk(probs, 2)
        top2_ids = top2.indices.tolist()
        top2_probs = top2.values.tolist()

        logit_gap = log_probs[top2_ids[0]].item() - log_probs[top2_ids[1]].item()

        natural_argmax_id = top2_ids[0]
        if len(steps) == 0 and first_step_override is not None:
            chosen_id = first_step_override
            rank_events.append(RankEvent(
                position=0,
                kind="injection",
                chosen_id=chosen_id,
                natural_argmax_id=natural_argmax_id,
            ))
        else:
            chosen_id = natural_argmax_id

        chosen_log_prob = log_probs[chosen_id].item()
        chosen_token = tokenizer.decode([chosen_id])

        if natural_argmax_id != chosen_id:
            alt_id = natural_argmax_id
            alt_prob = top2_probs[0]
        else:
            alt_id = top2_ids[1]
            alt_prob = top2_probs[1]
        alt_token = tokenizer.decode([alt_id])

        steps.append(StepRecord(
            token_id=chosen_id,
            token=chosen_token,
            log_prob=chosen_log_prob,
            entropy=entropy,
            alt_token_id=alt_id,
            alt_token=alt_token,
            alt_prob=alt_prob,
            logit_gap=logit_gap,
        ))
        history.append(chosen_id)

        for predicate in predicates:
            tag = predicate(history, steps, len(steps))
            if tag is not None:
                terminal_event = tag
                break

        if terminal_event is None:
            input_ids = torch.tensor([[chosen_id]], device=device)

    return Trajectory(
        stack=_capture_stack(model, model_revision),
        initial_ids=list(initial_ids),
        predicates=tuple(_spec_for(p) for p in predicates),
        inference_strategy=inference_strategy,
        steps=steps,
        rank_events=rank_events,
        terminal_event=terminal_event,
    )
