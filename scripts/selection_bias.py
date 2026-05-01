"""Selection-bias probe: extend broad-shallow ensemble to L_arch.

Re-runs the top-100 from `[BOS]` under the runtime basin-capture predicate,
with budget extended from 64 (broad-shallow) to L_arch=2048 under hard-cap
T=0. Adjudicates the open question raised by the v0.2 broad-shallow catalog:
do the 72/100 trajectories that reached budget_cap at depth 64 reach basins
by L_arch, or remain in transient?

Reports per-trajectory: terminal event, length, captured basin signature
(period, cycle text, late-window stats) when captured. Aggregates: capture
rate, capture-depth distribution, basin coalescence including any new
basins not in v0.2 catalog.

Run via: uv run python scripts/selection_bias.py
"""
from __future__ import annotations

from collections import Counter, defaultdict

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from peirce.basins import BasinSignature, basin_capture_predicate, detect_tail_cycle
from peirce.engine import generate_trajectory
from peirce.predicates import eos_predicate, window_cap_predicate
from peirce.records import Trajectory

MODEL_ID = "EleutherAI/pythia-1b-deduped"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
NUM_BRANCHES = 100
MAX_CYCLE_PERIOD = 32
CYCLE_WINDOW = 256
STATS_WINDOW = 256


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
            stats_window=STATS_WINDOW,
        ),
        window_cap_predicate(L_arch),
    ]

    print(
        f"BOS id: {bos_id}, EOS id: {eos_id}, L_arch: {L_arch}, branches: {NUM_BRANCHES}"
    )
    print(
        f"Basin probe: max_period={MAX_CYCLE_PERIOD}, "
        f"cycle_window={CYCLE_WINDOW}, stats_window={STATS_WINDOW}, K=4"
    )
    print(f"Top-{NUM_BRANCHES} BOS-mass total: {sum(branch_probs):.4f}\n")

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
        terminal = traj.terminal_event
        print(
            f"  ... [{i:3d}] {terminal:15s} len={traj.length:5d}",
            flush=True,
        )

    terminals = Counter(t.terminal_event for _, _, t, _ in results)
    print("\nTerminal event distribution:")
    for tag, n in terminals.most_common():
        print(f"  {tag}: {n}")

    captured = [(i, sig) for i, (_, _, _, sig) in enumerate(results) if sig is not None]
    print(f"  (basin-captured: {len(captured)}/{NUM_BRANCHES})\n")

    if captured:
        capture_lengths = [results[i][2].length for i, _ in captured]
        capture_lengths_sorted = sorted(capture_lengths)
        print(
            f"Capture-depth stats: "
            f"min={min(capture_lengths)} "
            f"median={capture_lengths_sorted[len(capture_lengths_sorted) // 2]} "
            f"mean={sum(capture_lengths) / len(capture_lengths):.1f} "
            f"max={max(capture_lengths)}"
        )
        bucket_64 = sum(1 for L in capture_lengths if L <= 64)
        bucket_256 = sum(1 for L in capture_lengths if 64 < L <= 256)
        bucket_1024 = sum(1 for L in capture_lengths if 256 < L <= 1024)
        bucket_more = sum(1 for L in capture_lengths if L > 1024)
        print(
            f"Capture-depth buckets: <=64: {bucket_64}, 65-256: {bucket_256}, "
            f"257-1024: {bucket_1024}, >1024: {bucket_more}"
        )
        print()

    print("Per-trajectory summary:")
    print("=" * 120)
    for i, (bid, bprob, traj, sig) in enumerate(results):
        branch = tokenizer.decode([bid])
        if sig is not None:
            cycle_tag = f"cyc={sig.period:2d} reps={sig.repetitions_in_cycle_window:2d}"
            stats_tag = (
                f"H={sig.late_window_mean_entropy:5.2f} "
                f"gap={sig.late_window_mean_logit_gap:5.2f}"
            )
            tail_text = sig.cycle_text
        else:
            cycle_tag = " " * 14
            stats_tag = " " * 17
            token_ids = [s.token_id for s in traj.steps]
            tail = token_ids[-64:] if len(token_ids) >= 64 else token_ids
            tail_text = tokenizer.decode(tail)
        print(
            f"[{i:3d}] {branch!r:>14} p={bprob:.4f} "
            f"{traj.terminal_event:15s} len={traj.length:5d} {cycle_tag} {stats_tag}  "
            f"{preview(tail_text)}"
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
        print(f"Total distinct basins: {len(sorted_basins)}\n")
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

    if terminals.get("window_cap"):
        print()
        print("Window-cap (uncaptured at L_arch) trajectories:")
        print("=" * 120)
        for i, (bid, bprob, traj, _) in enumerate(results):
            if traj.terminal_event != "window_cap":
                continue
            branch = tokenizer.decode([bid])
            token_ids = [s.token_id for s in traj.steps]
            tail = token_ids[-128:]
            print(
                f"  [{i:3d}] {branch!r:>14} p={bprob:.4f} "
                f"len={traj.length:5d}  tail: {preview(tokenizer.decode(tail))}"
            )


if __name__ == "__main__":
    main()
