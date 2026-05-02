"""First-cycle broad-shallow run with basin detection: top-100 from [BOS] x 64-token budget.

Generates the top-100 trajectories from the BOS distribution, each run under
hard-cap T=0 to a budget of 64 steps (or earlier EOS / window-cap). Applies
the v1 basin-detection probe (tail cycle period + late-window stats from
peirce.basins) to each trajectory, prints per-trajectory summaries, and
aggregates by basin identity (cycle token-id tuple) to surface basin
coalescence — distinct trajectories that landed in the same basin.

This is an eyeball pass at small scale; basin signatures are seeded into
basins.md as the first-cycle catalog.

Run via: uv run python scripts/broad_shallow.py
"""
from __future__ import annotations

from collections import Counter, defaultdict

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from peirce.basins import BasinSignature, basin_capture_predicate, detect_tail_cycle
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
CYCLE_WINDOW = 64
STATS_WINDOW = 32


def preview(text: str, width: int = 88) -> str:
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
        basin_capture_predicate(
            max_period=MAX_CYCLE_PERIOD,
            cycle_window=CYCLE_WINDOW,
        ),
        budget_cap_predicate(BUDGET),
        window_cap_predicate(L_arch),
    ]

    print(
        f"BOS id: {bos_id}, EOS id: {eos_id}, L_arch: {L_arch}, "
        f"budget: {BUDGET}, branches: {NUM_BRANCHES}"
    )
    print(
        f"Basin probe: max_period={MAX_CYCLE_PERIOD}, "
        f"cycle_window={CYCLE_WINDOW}, stats_window={STATS_WINDOW}"
    )
    print(f"Top-100 BOS-mass total: {sum(branch_probs):.4f}\n")

    results: list[tuple[int, float, Trajectory, BasinSignature | None]] = []
    for i, (bid, bprob) in enumerate(zip(branch_ids, branch_probs, strict=True)):
        traj = generate_trajectory(
            model=model,
            tokenizer=tokenizer,
            initial_ids=[bos_id],
            predicates=predicates,
            first_step_override=bid,
        )
        if traj.terminal_event == "candidate-basin":
            sig = detect_tail_cycle(
                traj.steps,
                max_period=MAX_CYCLE_PERIOD,
                cycle_window=CYCLE_WINDOW,
                stats_window=STATS_WINDOW,
            )
        else:
            sig = None
        results.append((bid, bprob, traj, sig))
        if (i + 1) % 10 == 0:
            print(f"  ... {i + 1}/{NUM_BRANCHES}", flush=True)

    terminals = Counter(t.terminal_event for _, _, t, _ in results)
    print("\nTerminal event distribution:")
    for tag, n in terminals.most_common():
        print(f"  {tag}: {n}")

    flagged = sum(1 for _, _, _, sig in results if sig is not None)
    print(f"  (basin-probe flagged: {flagged}/{NUM_BRANCHES})")
    print()

    print("Per-trajectory summary:")
    print("=" * 120)
    for i, (bid, bprob, traj, sig) in enumerate(results):
        branch = tokenizer.decode([bid])
        token_ids = [s.token_id for s in traj.steps]
        decoded = tokenizer.decode(token_ids)
        if sig is not None:
            cycle_tag = f"cyc={sig.period:2d}"
            stats_tag = (
                f"H={sig.late_window_mean_entropy:5.2f} "
                f"gap={sig.late_window_mean_logit_gap:5.2f}"
            )
        else:
            cycle_tag = "      "
            stats_tag = " " * 17
        print(
            f"[{i:3d}] {branch!r:>14} p={bprob:.4f} "
            f"{traj.terminal_event:11s} len={traj.length:3d} {cycle_tag} {stats_tag}  "
            f"{preview(decoded)}"
        )

    print()
    print("Basin coalescence (trajectories grouped by cycle token-id tuple):")
    print("=" * 120)
    basins: dict[tuple[int, ...], list[int]] = defaultdict(list)
    basin_sigs: dict[tuple[int, ...], BasinSignature] = {}
    for i, (_, _, _, sig) in enumerate(results):
        if sig is None:
            continue
        basins[sig.cycle_token_ids].append(i)
        basin_sigs[sig.cycle_token_ids] = sig

    if not basins:
        print("  (no basins flagged)")
    else:
        sorted_basins = sorted(basins.items(), key=lambda kv: -len(kv[1]))
        for cycle_ids, traj_ids in sorted_basins:
            sig = basin_sigs[cycle_ids]
            cycle_text_clean = sig.cycle_text.replace("\n", "\\n").replace("\t", "\\t")
            print(
                f"  basin period={sig.period:2d} reps={sig.repetitions_in_cycle_window:2d} "
                f"H={sig.late_window_mean_entropy:5.2f} "
                f"gap={sig.late_window_mean_logit_gap:5.2f} "
                f"trajectories={len(traj_ids)} {traj_ids}"
            )
            print(f"    cycle: {cycle_text_clean!r}")


if __name__ == "__main__":
    main()
