"""Representative-deep adjudication of candidates from broad-shallow.

Selected trajectory ranks 0, 4, 6, 14, 27, 28 from the broad-shallow ensemble.
Each is re-run at full architectural depth L_arch under hard-cap T=0 with the
runtime basin-capture predicate active. The question this script asks: do the
candidate cycles hold under the runtime predicate at L_arch budget? The
captured BasinSignature is reported for each trajectory.

Run via: uv run python scripts/representative_deep.py
"""
from __future__ import annotations

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from peirce.basins import basin_capture_predicate, detect_tail_cycle
from peirce.engine import generate_trajectory
from peirce.predicates import eos_predicate, window_cap_predicate

MODEL_ID = "EleutherAI/pythia-1b-deduped"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MAX_CYCLE_PERIOD = 32
CYCLE_WINDOW = 256
STATS_WINDOW = 256

SELECTED = [
    (0, "argmax of BOS — no broad-shallow cycle, escaped whitespace immediately"),
    (4, "10-space branch, broad-shallow cyc=4 (table fence)"),
    (6, "11-space branch, broad-shallow cyc=1 (pure space + |)"),
    (14, "7-space branch, broad-shallow cyc=2 (pipe-bar)"),
    (27, "24-space branch, broad-shallow cyc=1 (pure space)"),
    (28, "'_' branch, broad-shallow cyc=9 (semantic phrase)"),
]


def window_stats(values: list[float], n: int) -> tuple[float, float]:
    n = min(n, len(values))
    return sum(values[:n]) / n, sum(values[-n:]) / n


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
        topk = torch.topk(bos_probs, 100)
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
        f"L_arch: {L_arch}, candidates: {len(SELECTED)}, "
        f"basin probe: max_period={MAX_CYCLE_PERIOD} "
        f"cycle_window={CYCLE_WINDOW} stats_window={STATS_WINDOW} K=4\n"
    )

    for rank, narrative in SELECTED:
        bid = branch_ids[rank]
        bprob = branch_probs[rank]
        branch = tokenizer.decode([bid])
        print(f"[{rank}] {branch!r} (p={bprob:.4f}) — {narrative}")
        print(f"  generating up to L_arch={L_arch}...", flush=True)

        traj = generate_trajectory(
            model=model,
            tokenizer=tokenizer,
            initial_ids=[bos_id],
            predicates=predicates,
            first_step_override=bid,
        )

        log_probs = [s.log_prob for s in traj.steps]
        entropies = [s.entropy for s in traj.steps]
        alt_probs = [s.alt_prob for s in traj.steps]

        lp_early, lp_late = window_stats(log_probs, 64)
        H_early, H_late = window_stats(entropies, 64)
        ap_early, ap_late = window_stats(alt_probs, 64)

        print(f"  terminal: {traj.terminal_event}, length: {traj.length}")

        if traj.terminal_event == "candidate-basin":
            sig = detect_tail_cycle(
                traj.steps,
                max_period=MAX_CYCLE_PERIOD,
                cycle_window=CYCLE_WINDOW,
                stats_window=STATS_WINDOW,
            )
            cycle_text_clean = sig.cycle_text.replace("\n", "\\n").replace("\t", "\\t")
            print(
                f"  basin: period={sig.period} reps={sig.repetitions_in_cycle_window} "
                f"H={sig.late_window_mean_entropy:.3f} "
                f"gap={sig.late_window_mean_logit_gap:.3f}"
            )
            print(f"    cycle text: {cycle_text_clean!r}")
            print(f"    cycle token-ids: {sig.cycle_token_ids}")
        else:
            token_ids = [s.token_id for s in traj.steps]
            tail = token_ids[-128:] if len(token_ids) >= 128 else token_ids
            last_text = tokenizer.decode(tail).replace("\n", "\\n").replace("\t", "\\t")
            if len(last_text) > 400:
                last_text = last_text[:397] + "..."
            print(f"  last 128 tokens decoded: {last_text}")

        print(f"  log_prob  early avg={lp_early:7.3f}  late avg={lp_late:7.3f}")
        print(f"  entropy   early avg={H_early:.3f}    late avg={H_late:.3f}")
        print(f"  alt_prob  early avg={ap_early:.3f}    late avg={ap_late:.3f}")
        print()


if __name__ == "__main__":
    main()
