"""Parity check: KV-cache engine vs. full-context reference.

For each of NUM_BRANCHES top-k branches from [BOS], runs generate_trajectory
(KV-cache) and a local _generate_full_context reference (re-encodes the
whole history every step, matching the previous engine's behaviour).

Pass criterion is exact token-id identity, since the argmax sequence is
what defines a trajectory. Per-step scalars (log_prob, entropy, logit_gap)
are reported as informational diagnostics: at fp16 (Pythia-1B's native
dtype), KV-cache attention and full-context attention take different
reduction paths and diverge at a magnitude of ~1e-2 — both are equally
valid samplings of the same fp16-noisy computation. At fp32 the same
test gives ~1e-5 divergence.

Run via: uv run python scripts/smoke_kv_parity.py
"""
from __future__ import annotations

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from peirce.engine import _capture_stack, _spec_for, generate_trajectory
from peirce.predicates import (
    budget_cap_predicate,
    eos_predicate,
    window_cap_predicate,
)
from peirce.records import (
    InferenceStrategy,
    RankEvent,
    StepRecord,
    Trajectory,
)

MODEL_ID = "EleutherAI/pythia-1b-deduped"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
NUM_BRANCHES = 5
BUDGET = 16


@torch.no_grad()
def _generate_full_context(
    model,
    tokenizer,
    initial_ids,
    predicates,
    first_step_override=None,
):
    """Full-context reference: re-encodes the whole history each step."""
    device = next(model.parameters()).device
    history = list(initial_ids)
    steps: list[StepRecord] = []
    rank_events: list[RankEvent] = []
    terminal = None
    while terminal is None:
        input_ids = torch.tensor([history], device=device)
        logits = model(input_ids).logits[0, -1, :]
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
                position=0, kind="injection",
                chosen_id=chosen_id, natural_argmax_id=natural_argmax_id,
            ))
        else:
            chosen_id = natural_argmax_id
        chosen_log_prob = log_probs[chosen_id].item()
        chosen_token = tokenizer.decode([chosen_id])
        if natural_argmax_id != chosen_id:
            alt_id, alt_prob = natural_argmax_id, top2_probs[0]
        else:
            alt_id, alt_prob = top2_ids[1], top2_probs[1]
        alt_token = tokenizer.decode([alt_id])
        steps.append(StepRecord(
            token_id=chosen_id, token=chosen_token, log_prob=chosen_log_prob,
            entropy=entropy, alt_token_id=alt_id, alt_token=alt_token,
            alt_prob=alt_prob, logit_gap=logit_gap,
        ))
        history.append(chosen_id)
        for predicate in predicates:
            tag = predicate(history, steps, len(steps))
            if tag is not None:
                terminal = tag
                break
    return Trajectory(
        stack=_capture_stack(model, None),
        initial_ids=list(initial_ids),
        predicates=tuple(_spec_for(p) for p in predicates),
        inference_strategy=InferenceStrategy(name="hard_cap_t0", params={}),
        steps=steps,
        rank_events=rank_events,
        terminal_event=terminal,
    )


def main() -> None:
    print(f"Loading {MODEL_ID} on {DEVICE}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID).to(DEVICE).eval()

    bos_id = tokenizer.bos_token_id or tokenizer.eos_token_id
    eos_id = tokenizer.eos_token_id
    L_arch = model.config.max_position_embeddings

    with torch.no_grad():
        bos_logits = model(torch.tensor([[bos_id]], device=DEVICE)).logits[0, -1, :]
        bos_probs = torch.softmax(bos_logits, dim=-1)
        topk = torch.topk(bos_probs, NUM_BRANCHES)
        branch_ids = topk.indices.tolist()

    predicates = [
        eos_predicate(eos_id),
        budget_cap_predicate(BUDGET),
        window_cap_predicate(L_arch),
    ]

    all_match = True
    for i, bid in enumerate(branch_ids):
        traj_kv = generate_trajectory(
            model=model, tokenizer=tokenizer, initial_ids=[bos_id],
            predicates=predicates, first_step_override=bid,
        )
        traj_ref = _generate_full_context(
            model=model, tokenizer=tokenizer, initial_ids=[bos_id],
            predicates=predicates, first_step_override=bid,
        )
        ids_kv = [s.token_id for s in traj_kv.steps]
        ids_ref = [s.token_id for s in traj_ref.steps]
        ids_match = ids_kv == ids_ref
        max_lp_diff = 0.0
        max_H_diff = 0.0
        max_gap_diff = 0.0
        if ids_match:
            for s_kv, s_ref in zip(traj_kv.steps, traj_ref.steps, strict=True):
                max_lp_diff = max(max_lp_diff, abs(s_kv.log_prob - s_ref.log_prob))
                max_H_diff = max(max_H_diff, abs(s_kv.entropy - s_ref.entropy))
                max_gap_diff = max(max_gap_diff, abs(s_kv.logit_gap - s_ref.logit_gap))
        all_match = all_match and ids_match
        flag = "OK " if ids_match else "FAIL"
        print(
            f"[{flag}] branch {i} bid={bid}: "
            f"kv_len={traj_kv.length} ref_len={traj_ref.length} "
            f"ids_match={ids_match} "
            f"max_lp_diff={max_lp_diff:.2e} max_H_diff={max_H_diff:.2e} "
            f"max_gap_diff={max_gap_diff:.2e}"
        )
        if not ids_match:
            print(f"  kv  ids: {ids_kv}")
            print(f"  ref ids: {ids_ref}")
    print()
    print("PARITY OK" if all_match else "PARITY FAILED")

    # Manifest sanity-print: confirm provenance fields populate on the first
    # KV trajectory.
    print()
    print("Manifest sanity-print (first KV trajectory):")
    sample = generate_trajectory(
        model=model, tokenizer=tokenizer, initial_ids=[bos_id],
        predicates=predicates, first_step_override=branch_ids[0],
    )
    print(f"  stack: {sample.stack}")
    print(f"  initial_ids: {sample.initial_ids}")
    print(f"  predicates: {sample.predicates}")
    print(f"  inference_strategy: {sample.inference_strategy}")
    print(f"  rank_events: {sample.rank_events}")
    print(f"  terminal_event: {sample.terminal_event} (position={sample.length})")


if __name__ == "__main__":
    main()
