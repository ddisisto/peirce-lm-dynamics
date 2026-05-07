"""Extend all top-100-from-BOS trajectories to L_arch=2048, predicate-free.

Re-runs the top-100 from `[BOS]` under predicates `[eos, window_cap(L_arch)]`
only — no basin_capture. Cache-hits the existing trajectory rows produced by
broad_shallow / selection_bias; the engine prefills from each trajectory's
existing materialized steps (4–2047) and inferences only the new positions.
Hard-cap T=0 inference, fp16 — same stack identity as the existing rows.

Motivation: the existing selection-bias observations have *truncated* tails
for the 63 cycle-captured trajectories (lengths 4–575). The v1 basin_capture
predicate stops generation at K=4 cycle confirmation, so we have no data on
what happens past that point. Two open questions resolve under full-depth
data:

- Does v1-captured trajectory entropy stay low past capture, or does it
  drift / loosen? (Bears on whether v2's entropy floor is a depth phenomenon
  or a basin phenomenon.)
- Do the very-short v1 captures (lengths 4–17) actually settle into a
  stable basin, or did v1's K=4 fire prematurely on a borderline structural
  cycle?

Persists fresh observation rows under the simpler predicate set; the
trajectory rows themselves are shared with selection_bias / broad_shallow
via content-addressed identity. After this run, all 100 trajectories have
2047 materialized steps in `data/peirce.db` and downstream analysis runs
read-only over the store with no further inference.

NUM_BRANCHES can be overridden via FULL_DEPTH_TOP_K for smoke runs.

Run via: uv run python scripts/full_depth_extension.py
"""
from __future__ import annotations

import os
import time
from collections import Counter

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from peirce.predicates import eos_predicate, window_cap_predicate
from peirce.records import Injection
from peirce.runner import default_store_path, observe
from peirce.store import open_store

MODEL_ID = "EleutherAI/pythia-1b-deduped"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
NUM_BRANCHES = int(os.environ.get("FULL_DEPTH_TOP_K", "100"))


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
        window_cap_predicate(L_arch),
    ]

    store_path = default_store_path()
    store = open_store(store_path)
    print(f"Store: {store_path}")
    print(
        f"BOS id: {bos_id}, EOS id: {eos_id}, L_arch: {L_arch}, branches: {NUM_BRANCHES}"
    )
    print(f"Predicates: [eos, window_cap] (no basin_capture — extend all to L_arch)")
    print(f"Top-{NUM_BRANCHES} BOS-mass total: {sum(branch_probs):.4f}\n")

    n_cached = 0
    n_extended = 0
    terminals: Counter[str] = Counter()
    lengths: list[int] = []

    t_start = time.perf_counter()
    for i, (bid, bprob) in enumerate(zip(branch_ids, branch_probs, strict=True)):
        t_obs = time.perf_counter()
        obs = observe(
            store, model, tokenizer,
            initial_ids=[bos_id],
            predicates=predicates,
            injections=(Injection(position=0, chosen_id=bid),),
        )
        elapsed = time.perf_counter() - t_obs
        if elapsed < 0.05:
            n_cached += 1
        else:
            n_extended += 1
        terminals[obs.terminal_event] += 1
        lengths.append(obs.length)
        print(
            f"  ... [{i:3d}] {obs.terminal_event:11s} len={obs.length:5d}  "
            f"({elapsed:7.2f}s)",
            flush=True,
        )

    t_total = time.perf_counter() - t_start
    print()
    print(f"Total: {t_total:.1f}s  cache={n_cached}  extended={n_extended}")
    print(f"Terminal events: {dict(terminals)}")
    if lengths:
        sl = sorted(lengths)
        print(
            f"Length stats: min={min(lengths)} "
            f"median={sl[len(sl) // 2]} mean={sum(lengths) / len(lengths):.1f} "
            f"max={max(lengths)}"
        )


if __name__ == "__main__":
    main()
