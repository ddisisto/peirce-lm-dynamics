"""Representative-deep adjudication of candidates from broad-shallow.

Selected trajectory ids 0, 4, 6, 14, 27, 28 from the broad-shallow baseline
at commit d18c693. Each is re-run at full architectural depth L_arch under
hard-cap T=0; same engine, EOS and window-cap as the only predicates. The
question this script asks: do the candidate cycles flagged at depth 64
hold near depth ~L_arch, or do they escape?

Run via: uv run python scripts/representative_deep.py
"""
from __future__ import annotations

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from peirce.engine import generate_trajectory
from peirce.predicates import eos_predicate, window_cap_predicate

MODEL_ID = "EleutherAI/pythia-1b-deduped"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

SELECTED = [
    (0, "argmax of BOS — no broad-shallow cycle, escaped whitespace immediately"),
    (4, "10-space branch, broad-shallow cyc=4 (table fence)"),
    (6, "11-space branch, broad-shallow cyc=1 (pure space + |)"),
    (14, "7-space branch, broad-shallow cyc=2 (pipe-bar)"),
    (27, "24-space branch, broad-shallow cyc=1 (pure space)"),
    (28, "'_' branch, broad-shallow cyc=9 (semantic phrase)"),
]


def detect_tail_cycle(token_ids: list[int], max_period: int = 32) -> int | None:
    n = len(token_ids)
    for p in range(1, min(max_period, n // 2) + 1):
        if token_ids[-p:] == token_ids[-2 * p : -p]:
            return p
    return None


def window_stats(values: list[float], n: int) -> tuple[float, float]:
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
        window_cap_predicate(L_arch),
    ]

    print(f"L_arch: {L_arch}, candidates: {len(SELECTED)}\n")

    for rank, narrative in SELECTED:
        bid = branch_ids[rank]
        bprob = branch_probs[rank]
        branch = tokenizer.decode([bid])
        print(f"[{rank}] {branch!r} (p={bprob:.4f}) — {narrative}")
        print(f"  generating to L_arch={L_arch}...", flush=True)

        traj = generate_trajectory(
            model=model,
            tokenizer=tokenizer,
            initial_ids=[bos_id],
            predicates=predicates,
            first_step_override=bid,
        )

        token_ids = [s.token_id for s in traj.steps]
        log_probs = [s.log_prob for s in traj.steps]
        entropies = [s.entropy for s in traj.steps]
        alt_probs = [s.alt_prob for s in traj.steps]

        tail_window = token_ids[-256:] if len(token_ids) >= 256 else token_ids
        tail_cycle = detect_tail_cycle(tail_window)

        lp_early, lp_late = window_stats(log_probs, 64)
        H_early, H_late = window_stats(entropies, 64)
        ap_early, ap_late = window_stats(alt_probs, 64)

        last_text = tokenizer.decode(token_ids[-128:])
        clean = last_text.replace("\n", "\\n").replace("\t", "\\t")
        if len(clean) > 400:
            clean = clean[:397] + "..."

        print(f"  terminal: {traj.terminal_event}, length: {traj.length}")
        print(f"  tail cycle (last 256 tokens, max_period 32): {tail_cycle}")
        print(f"  log_prob  early avg={lp_early:7.3f}  late avg={lp_late:7.3f}")
        print(f"  entropy   early avg={H_early:.3f}    late avg={H_late:.3f}")
        print(f"  alt_prob  early avg={ap_early:.3f}    late avg={ap_late:.3f}")
        print(f"  last 128 tokens decoded:")
        print(f"    {clean}")
        print()


if __name__ == "__main__":
    main()
