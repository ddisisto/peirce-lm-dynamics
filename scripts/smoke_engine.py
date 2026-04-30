"""Smoke test for the trajectory engine.

Generates a few short trajectories from BOS using top-k branching, prints
each trajectory's tokens and per-step thin records to stdout. Validates the
engine end-to-end before persistence is wired up.

Run via: uv run python scripts/smoke_engine.py
"""
from __future__ import annotations

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from peirce.engine import generate_trajectory
from peirce.predicates import (
    budget_cap_predicate,
    eos_predicate,
    window_cap_predicate,
)

MODEL_ID = "EleutherAI/pythia-1b-deduped"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
NUM_BRANCHES = 5
BUDGET = 16


def main() -> None:
    print(f"Loading {MODEL_ID} on {DEVICE}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID).to(DEVICE).eval()

    bos_id = tokenizer.bos_token_id
    if bos_id is None:
        bos_id = tokenizer.eos_token_id
    eos_id = tokenizer.eos_token_id
    L_arch = model.config.max_position_embeddings

    with torch.no_grad():
        bos_logits = model(torch.tensor([[bos_id]], device=DEVICE)).logits[0, -1, :]
        bos_probs = torch.softmax(bos_logits, dim=-1)
        topk = torch.topk(bos_probs, NUM_BRANCHES)
        branch_ids = topk.indices.tolist()
        branch_probs = topk.values.tolist()

    predicates = [
        eos_predicate(eos_id),
        budget_cap_predicate(BUDGET),
        window_cap_predicate(L_arch),
    ]

    print(
        f"BOS id: {bos_id}, EOS id: {eos_id}, L_arch: {L_arch}, "
        f"budget: {BUDGET}, branches: {NUM_BRANCHES}\n"
    )

    for i, (branch_id, branch_prob) in enumerate(zip(branch_ids, branch_probs, strict=True)):
        traj = generate_trajectory(
            model=model,
            tokenizer=tokenizer,
            initial_ids=[bos_id],
            predicates=predicates,
            first_step_override=branch_id,
        )
        branch_token = tokenizer.decode([branch_id])
        print(
            f"Trajectory {i}: branch {branch_token!r} (p={branch_prob:.4f}) "
            f"-> terminal={traj.terminal_event}, length={traj.length}"
        )
        for step_idx, step in enumerate(traj.steps):
            print(
                f"  step {step_idx:2d}: tok={step.token!r:>16} "
                f"lp={step.log_prob:7.3f}  H={step.entropy:.3f}  "
                f"top2={step.top2_token!r:>16} p={step.top2_prob:.3f}"
            )
        print()


if __name__ == "__main__":
    main()
