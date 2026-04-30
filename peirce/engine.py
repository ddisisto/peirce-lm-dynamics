"""Trajectory generation under hard-cap T=0 inference.

Generates a trajectory by appending one argmax token at a time to the running
context, recording per-step thin records, until a terminal event fires. The
first step may be overridden to enable top-k-from-BOS branching: at step 0,
a forced token is chosen instead of the argmax, but its position in the
distribution is recorded normally (log-probability, entropy, top-2).
"""
from __future__ import annotations

from typing import Sequence

import torch
from transformers import PreTrainedModel, PreTrainedTokenizerBase

from .predicates import Predicate
from .records import StepRecord, Trajectory


@torch.no_grad()
def generate_trajectory(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizerBase,
    initial_ids: Sequence[int],
    predicates: Sequence[Predicate],
    first_step_override: int | None = None,
) -> Trajectory:
    device = next(model.parameters()).device
    history: list[int] = list(initial_ids)
    steps: list[StepRecord] = []
    terminal_event: str | None = None

    while terminal_event is None:
        input_ids = torch.tensor([history], device=device)
        logits = model(input_ids).logits[0, -1, :]
        log_probs = torch.log_softmax(logits, dim=-1)
        probs = log_probs.exp()
        entropy = -(probs * log_probs).sum().item()

        top2 = torch.topk(probs, 2)
        top2_ids = top2.indices.tolist()
        top2_probs = top2.values.tolist()

        if len(steps) == 0 and first_step_override is not None:
            chosen_id = first_step_override
        else:
            chosen_id = top2_ids[0]

        chosen_log_prob = log_probs[chosen_id].item()
        chosen_token = tokenizer.decode([chosen_id])
        runner_id = top2_ids[1]
        runner_token = tokenizer.decode([runner_id])
        runner_prob = top2_probs[1]

        steps.append(StepRecord(
            token_id=chosen_id,
            token=chosen_token,
            log_prob=chosen_log_prob,
            entropy=entropy,
            top2_token_id=runner_id,
            top2_token=runner_token,
            top2_prob=runner_prob,
        ))
        history.append(chosen_id)

        for predicate in predicates:
            tag = predicate(history, len(steps))
            if tag is not None:
                terminal_event = tag
                break

    return Trajectory(
        initial_ids=list(initial_ids),
        steps=steps,
        terminal_event=terminal_event,
    )
