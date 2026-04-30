"""First-cycle broad-shallow run: top-100 from [BOS] x 64-token budget.

Generates the top-100 trajectories from the BOS distribution, each run under
hard-cap T=0 to a budget of 64 steps (or earlier EOS / window-cap). Prints
an aggregate summary of terminal events and a one-line per-trajectory
summary including a post-hoc structural-cycle annotation.

This is an eyeball pass before persistence is wired up. No artifacts on disk;
the goal is to surface what the ensemble actually looks like, so that
schema decisions for Phase 1 are informed by observation rather than guess.

Run via: uv run python scripts/broad_shallow.py
"""
from __future__ import annotations

from collections import Counter

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from peirce.engine import generate_trajectory
from peirce.predicates import (
    budget_cap_predicate,
    eos_predicate,
    window_cap_predicate,
)
from peirce.records import Trajectory

MODEL_ID = "EleutherAI/pythia-1b-deduped"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
NUM_BRANCHES = 100
BUDGET = 64
MAX_CYCLE_PERIOD = 16


def detect_tail_cycle(token_ids: list[int], max_period: int = MAX_CYCLE_PERIOD) -> int | None:
    """Return smallest period p in [1, max_period] for which the last p tokens
    repeat the p tokens before that. None if no such repeat is found.
    """
    n = len(token_ids)
    for p in range(1, min(max_period, n // 2) + 1):
        if token_ids[-p:] == token_ids[-2 * p : -p]:
            return p
    return None


def preview(text: str, width: int = 90) -> str:
    rendered = text.replace("\n", "\\n").replace("\t", "\\t")
    if len(rendered) > width:
        rendered = rendered[: width - 3] + "..."
    return rendered


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
        f"budget: {BUDGET}, branches: {NUM_BRANCHES}"
    )
    print(f"Top-100 BOS-mass total: {sum(branch_probs):.4f}\n")

    results: list[tuple[int, float, Trajectory]] = []
    for i, (bid, bprob) in enumerate(zip(branch_ids, branch_probs, strict=True)):
        traj = generate_trajectory(
            model=model,
            tokenizer=tokenizer,
            initial_ids=[bos_id],
            predicates=predicates,
            first_step_override=bid,
        )
        results.append((bid, bprob, traj))
        if (i + 1) % 10 == 0:
            print(f"  ... {i + 1}/{NUM_BRANCHES}", flush=True)

    terminals = Counter(t.terminal_event for _, _, t in results)
    print("\nTerminal event distribution:")
    for tag, n in terminals.most_common():
        print(f"  {tag}: {n}")

    cycle_count = sum(
        1 for _, _, t in results if detect_tail_cycle([s.token_id for s in t.steps]) is not None
    )
    print(f"  (post-hoc tail-cycle flagged: {cycle_count})")
    print()

    print("Per-trajectory summary:")
    print("=" * 110)
    for i, (bid, bprob, traj) in enumerate(results):
        branch = tokenizer.decode([bid])
        token_ids = [s.token_id for s in traj.steps]
        decoded = tokenizer.decode(token_ids)
        period = detect_tail_cycle(token_ids)
        cycle_tag = f"cyc={period}" if period is not None else "      "
        print(
            f"[{i:3d}] {branch!r:>14} p={bprob:.4f} "
            f"{traj.terminal_event:11s} len={traj.length:3d} {cycle_tag}  "
            f"{preview(decoded)}"
        )


if __name__ == "__main__":
    main()
