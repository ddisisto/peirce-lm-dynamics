"""Smoke test for Pythia-1B-deduped: load model, compute L=1 next-token
logits for a handful of single-token contexts, print top-k successors.

Validates the inference path and the BOS+single-token convention before
the L=1 sweep proper.

Run via: uv run python scripts/smoke_l1.py
"""

from __future__ import annotations

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "EleutherAI/pythia-1b-deduped"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
TOP_K = 5

# Tokens to probe — a handful chosen for legibility, not for coverage.
PROBE_STRINGS = [
    " the",
    " of",
    " a",
    " is",
    " and",
    " in",
    "\n",
    ".",
    "I",
    "He",
]


def main() -> None:
    print(f"Loading {MODEL_ID} on {DEVICE}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID).to(DEVICE).eval()

    bos_id = tokenizer.bos_token_id
    if bos_id is None:
        # GPT-NeoX tokenizer uses <|endoftext|> as both bos and eos.
        bos_id = tokenizer.eos_token_id
    print(f"BOS token id: {bos_id} ({tokenizer.decode([bos_id])!r})")
    print(f"Vocab size: {len(tokenizer)}")
    print(
        f"Convention: [BOS, single_token] -> last-position logits, top-{TOP_K} successors\n"
    )

    probes: list[tuple[str, int]] = []
    for s in PROBE_STRINGS:
        ids = tokenizer.encode(s, add_special_tokens=False)
        if len(ids) != 1:
            print(f"  skip {s!r}: encoded to {ids} (not single token)")
            continue
        probes.append((s, ids[0]))

    input_ids = torch.tensor(
        [[bos_id, tok_id] for _, tok_id in probes], device=DEVICE
    )
    with torch.no_grad():
        logits = model(input_ids).logits  # [batch, seq, vocab]
    last_logits = logits[:, -1, :]
    probs = torch.softmax(last_logits, dim=-1)
    topk = torch.topk(probs, TOP_K, dim=-1)

    for (s, tok_id), top_indices, top_probs in zip(
        probes, topk.indices, topk.values, strict=True
    ):
        decoded = [tokenizer.decode([i.item()]) for i in top_indices]
        print(f"[BOS] {s!r} (id={tok_id}):")
        for d, p in zip(decoded, top_probs, strict=True):
            print(f"    {p.item():.4f}  {d!r}")
        print()


if __name__ == "__main__":
    main()
