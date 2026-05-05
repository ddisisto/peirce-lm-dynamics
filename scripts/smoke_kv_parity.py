"""Parity check: KV-cache engine vs. full-context reference.

For each of NUM_BRANCHES top-k branches from [BOS], runs observe_trajectory
(KV-cache + prefill) and a local _generate_full_context reference (re-encodes
the whole history every step, matching the pre-KV-cache engine's behaviour).

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

from peirce.engine import (
    _capture_stack,
    _spec_for,
    fresh_trajectory,
    observe_trajectory,
)
from peirce.predicates import (
    budget_cap_predicate,
    eos_predicate,
    window_cap_predicate,
)
from peirce.records import (
    InferenceStrategy,
    Injection,
    Observation,
    StepRecord,
    Trajectory,
)

MODEL_ID = "EleutherAI/pythia-1b-deduped"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
NUM_BRANCHES = 5
BUDGET = 16


@torch.no_grad()
def _observe_full_context(
    model,
    tokenizer,
    trajectory: Trajectory,
    predicates,
) -> Observation:
    """Full-context reference: re-encodes the whole history each step.

    Matches the pre-KV-cache engine, including injection handling. Used
    as the parity reference for observe_trajectory's prefill+KV path.
    """
    device = next(model.parameters()).device
    full_history = list(trajectory.initial_ids)
    for s in trajectory.steps:
        full_history.append(s.token_id)
    injection_at = {inj.position: inj.chosen_id for inj in trajectory.injections}
    pred_specs = tuple(_spec_for(p) for p in predicates)
    inference_strategy = InferenceStrategy(name="hard_cap_t0", params={})
    terminal = None
    while terminal is None:
        input_ids = torch.tensor([full_history], device=device)
        logits = model(input_ids).logits[0, -1, :]
        log_probs = torch.log_softmax(logits, dim=-1)
        probs = log_probs.exp()
        entropy = -(probs * log_probs).sum().item()
        top2 = torch.topk(probs, 2)
        top2_ids = top2.indices.tolist()
        top2_probs = top2.values.tolist()
        logit_gap = log_probs[top2_ids[0]].item() - log_probs[top2_ids[1]].item()
        natural_argmax_id = top2_ids[0]
        position = len(trajectory.steps)
        chosen_id = injection_at.get(position, natural_argmax_id)
        chosen_log_prob = log_probs[chosen_id].item()
        chosen_token = tokenizer.decode([chosen_id])
        if natural_argmax_id != chosen_id:
            alt_id, alt_prob = natural_argmax_id, top2_probs[0]
        else:
            alt_id, alt_prob = top2_ids[1], top2_probs[1]
        alt_token = tokenizer.decode([alt_id])
        trajectory.steps.append(StepRecord(
            token_id=chosen_id, token=chosen_token, log_prob=chosen_log_prob,
            entropy=entropy, alt_token_id=alt_id, alt_token=alt_token,
            alt_prob=alt_prob, logit_gap=logit_gap,
        ))
        full_history.append(chosen_id)
        for predicate in predicates:
            tag = predicate(full_history, trajectory.steps, len(trajectory.steps))
            if tag is not None:
                terminal = tag
                break
    return Observation(
        trajectory=trajectory,
        predicates=pred_specs,
        inference_strategy=inference_strategy,
        terminal_event=terminal,
        observed_length=len(trajectory.steps),
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
        traj_kv = fresh_trajectory(
            model, [bos_id], injections=(Injection(position=0, chosen_id=bid),),
        )
        obs_kv = observe_trajectory(model, tokenizer, traj_kv, predicates)
        traj_ref = fresh_trajectory(
            model, [bos_id], injections=(Injection(position=0, chosen_id=bid),),
        )
        obs_ref = _observe_full_context(model, tokenizer, traj_ref, predicates)
        ids_kv = [s.token_id for s in obs_kv.steps]
        ids_ref = [s.token_id for s in obs_ref.steps]
        ids_match = ids_kv == ids_ref
        max_lp_diff = 0.0
        max_H_diff = 0.0
        max_gap_diff = 0.0
        if ids_match:
            for s_kv, s_ref in zip(obs_kv.steps, obs_ref.steps, strict=True):
                max_lp_diff = max(max_lp_diff, abs(s_kv.log_prob - s_ref.log_prob))
                max_H_diff = max(max_H_diff, abs(s_kv.entropy - s_ref.entropy))
                max_gap_diff = max(max_gap_diff, abs(s_kv.logit_gap - s_ref.logit_gap))
        all_match = all_match and ids_match
        flag = "OK " if ids_match else "FAIL"
        print(
            f"[{flag}] branch {i} bid={bid}: "
            f"kv_len={obs_kv.length} ref_len={obs_ref.length} "
            f"ids_match={ids_match} "
            f"max_lp_diff={max_lp_diff:.2e} max_H_diff={max_H_diff:.2e} "
            f"max_gap_diff={max_gap_diff:.2e}"
        )
        if not ids_match:
            print(f"  kv  ids: {ids_kv}")
            print(f"  ref ids: {ids_ref}")
    print()
    print("PARITY OK" if all_match else "PARITY FAILED")


if __name__ == "__main__":
    main()
