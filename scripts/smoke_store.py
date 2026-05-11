"""Round-trip smoke test for the SQLite trajectory/observation store.

Exercises:
- write + read of a single observation, with field-by-field equality
- idempotent re-write (same observation_id, no duplicate rows)
- step storage de-duplication: two observations of the same trajectory at
  different budgets share trajectory_steps
- trajectory extension via the engine's prefill path: a longer-budget
  observation extends an already-stored shorter one
- short-budget shortcut: a smaller-budget observation against a
  longer-stored trajectory terminates within the existing prefix without
  any inference
- runner cache hit: re-requesting the same observation reads it from the
  store rather than re-running
- position-N>0 injection (C2 branching path): branch from a parent
  trajectory at mid-trajectory position, validates prefix preservation,
  injection forcing, alt-field semantics at the injection step, and
  identity-distinct trajectory_id

Run: uv run python scripts/smoke_store.py
"""
from __future__ import annotations

import tempfile
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from peirce.engine import (
    fresh_trajectory,
    observe_trajectory,
)
from peirce.predicates import (
    budget_cap_predicate,
    eos_predicate,
    window_cap_predicate,
)
from peirce.records import Injection
from peirce.runner import observe
from peirce.store import (
    find_trajectory,
    observation_hash,
    open_store,
    query_observations,
    read_observation,
    trajectory_hash,
    write_observation,
)

MODEL_ID = "EleutherAI/pythia-1b-deduped"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def _observations_equal(a, b) -> tuple[bool, str]:
    if a.trajectory.stack != b.trajectory.stack:
        return False, "stack mismatch"
    if a.trajectory.initial_ids != b.trajectory.initial_ids:
        return False, f"initial_ids: {a.trajectory.initial_ids} vs {b.trajectory.initial_ids}"
    if a.trajectory.injections != b.trajectory.injections:
        return False, f"injections: {a.trajectory.injections} vs {b.trajectory.injections}"
    if a.predicates != b.predicates:
        return False, f"predicates: {a.predicates} vs {b.predicates}"
    if a.inference_strategy != b.inference_strategy:
        return False, f"inference_strategy: {a.inference_strategy} vs {b.inference_strategy}"
    if a.terminal_event != b.terminal_event:
        return False, f"terminal_event: {a.terminal_event} vs {b.terminal_event}"
    if a.observed_length != b.observed_length:
        return False, f"observed_length: {a.observed_length} vs {b.observed_length}"
    if len(a.steps) != len(b.steps):
        return False, f"step count: {len(a.steps)} vs {len(b.steps)}"
    for i, (sa, sb) in enumerate(zip(a.steps, b.steps, strict=True)):
        if sa != sb:
            return False, f"step {i} mismatch:\n  a={sa}\n  b={sb}"
    return True, ""


def main() -> None:
    print(f"Loading {MODEL_ID} on {DEVICE}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID).to(DEVICE).eval()

    bos_id = tokenizer.bos_token_id or tokenizer.eos_token_id
    eos_id = tokenizer.eos_token_id
    L_arch = model.config.max_position_embeddings

    def preds(budget: int):
        return [
            eos_predicate(eos_id),
            budget_cap_predicate(budget),
            window_cap_predicate(L_arch),
        ]

    with tempfile.TemporaryDirectory() as td:
        conn = open_store(Path(td) / "smoke.db")

        # === 1: basic round-trip ===
        print("\n[1] Generate, write, read, equality check...")
        traj = fresh_trajectory(model, [bos_id])
        obs = observe_trajectory(model, tokenizer, traj, preds(8))
        oid = write_observation(conn, obs)
        print(f"  observation_id={oid}")
        obs_round = read_observation(conn, oid)
        eq, diff = _observations_equal(obs, obs_round)
        assert eq, f"round-trip failed: {diff}"
        print("  OK")

        # === 2: idempotent re-write ===
        print("\n[2] Re-write same observation, check no duplicate rows...")
        oid2 = write_observation(conn, obs)
        assert oid == oid2
        n_obs = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        n_traj = conn.execute("SELECT COUNT(*) FROM trajectories").fetchone()[0]
        n_steps = conn.execute("SELECT COUNT(*) FROM trajectory_steps").fetchone()[0]
        assert n_obs == 1 and n_traj == 1 and n_steps == 8, \
            f"row counts off: obs={n_obs} traj={n_traj} steps={n_steps}"
        print(f"  OK — observations=1 trajectories=1 steps=8")

        # === 3: extension via second observation at larger budget ===
        print("\n[3] Larger-budget observation extends the same trajectory...")
        traj_ext = find_trajectory(conn, fresh_trajectory(model, [bos_id]))
        assert traj_ext is not None and len(traj_ext.steps) == 8
        obs_ext = observe_trajectory(model, tokenizer, traj_ext, preds(16))
        assert obs_ext.observed_length == 16
        assert len(traj_ext.steps) == 16  # mutated in place
        # First 8 steps should be byte-identical to the original observation.
        for i in range(8):
            assert obs_ext.steps[i] == obs.steps[i], f"prefix divergence at step {i}"
        oid_ext = write_observation(conn, obs_ext)
        n_traj = conn.execute("SELECT COUNT(*) FROM trajectories").fetchone()[0]
        n_steps = conn.execute("SELECT COUNT(*) FROM trajectory_steps").fetchone()[0]
        n_obs = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        assert n_traj == 1 and n_steps == 16 and n_obs == 2, \
            f"extension row counts off: traj={n_traj} steps={n_steps} obs={n_obs}"
        print(f"  OK — trajectories=1 steps=16 (was 8) observations=2")

        # === 4: short-budget shortcut, no inference ===
        print("\n[4] Short-budget observation, fires within stored prefix, no inference...")
        traj_short = find_trajectory(conn, fresh_trajectory(model, [bos_id]))
        assert traj_short is not None and len(traj_short.steps) == 16
        t0 = time.perf_counter()
        obs_short = observe_trajectory(model, tokenizer, traj_short, preds(4))
        elapsed = time.perf_counter() - t0
        assert obs_short.observed_length == 4
        assert obs_short.terminal_event == "budget_cap"
        # Steps view should be the first 4 of the stored 16; trajectory not extended.
        assert len(traj_short.steps) == 16, "short-budget observation should not extend"
        print(f"  OK — observed_length=4, terminal=budget_cap, elapsed={elapsed*1000:.1f}ms")

        # === 5: runner cache hit ===
        print("\n[5] Runner observe(), second call should hit the cache...")
        obs_a = observe(conn, model, tokenizer, initial_ids=[bos_id], predicates=preds(8))
        t0 = time.perf_counter()
        obs_b = observe(conn, model, tokenizer, initial_ids=[bos_id], predicates=preds(8))
        elapsed = time.perf_counter() - t0
        eq, diff = _observations_equal(obs_a, obs_b)
        assert eq, f"runner cache divergence: {diff}"
        # Should be sub-50ms — pure DB read, no inference.
        assert elapsed < 0.5, f"cache hit too slow ({elapsed*1000:.1f}ms), suspicious"
        print(f"  OK — cached read in {elapsed*1000:.1f}ms")

        # === 6: injection round-trip ===
        print("\n[6] Injection trajectory round-trip + identity-distinct from non-injection...")
        with torch.no_grad():
            bos_logits = model(torch.tensor([[bos_id]], device=DEVICE)).logits[0, -1, :]
            top2 = torch.topk(torch.softmax(bos_logits, dim=-1), 2)
            override_id = top2.indices.tolist()[1]
        traj_inj = fresh_trajectory(
            model, [bos_id],
            injections=(Injection(position=0, chosen_id=override_id),),
        )
        obs_inj = observe_trajectory(model, tokenizer, traj_inj, preds(8))
        # Must have a different trajectory_id than the non-injection version.
        traj_no_inj = fresh_trajectory(model, [bos_id])
        assert trajectory_hash(traj_inj) != trajectory_hash(traj_no_inj), \
            "injection trajectory must have a distinct trajectory_id"
        oid_inj = write_observation(conn, obs_inj)
        assert observation_hash(obs_inj) != observation_hash(obs)
        obs_inj_round = read_observation(conn, oid_inj)
        eq, diff = _observations_equal(obs_inj, obs_inj_round)
        assert eq, f"injection round-trip failed: {diff}"
        print("  OK")

        # === 7: position-N>0 injection (C2 branching path) ===
        print("\n[7] Position-N>0 injection: branch from parent at mid-trajectory position...")
        branch_position = 4
        parent_step = obs.steps[branch_position]
        branch_alt_id = parent_step.alt_token_id
        traj_branch = fresh_trajectory(
            model, [bos_id],
            injections=(Injection(position=branch_position, chosen_id=branch_alt_id),),
        )
        obs_branch = observe_trajectory(model, tokenizer, traj_branch, preds(8))
        # Branch has a distinct trajectory_id from the no-injection parent.
        assert trajectory_hash(traj_branch) != trajectory_hash(obs.trajectory), \
            "branch trajectory must have distinct trajectory_id from parent"
        # Prefix [0, branch_position) is byte-identical to parent — no injection
        # takes effect before branch_position, so deterministic argmax agrees.
        for i in range(branch_position):
            assert obs_branch.steps[i] == obs.steps[i], \
                f"branch prefix divergence at step {i} (should match parent before injection)"
        # Step at branch_position has chosen_id == the injected alt_id.
        assert obs_branch.steps[branch_position].token_id == branch_alt_id, \
            f"branch step at injection position should be alt_id={branch_alt_id}, " \
            f"got {obs_branch.steps[branch_position].token_id}"
        # Alt at injection step is the natural argmax (= parent's chosen at that position).
        assert obs_branch.steps[branch_position].alt_token_id == parent_step.token_id, \
            "branch alt at injection step should be parent's natural argmax"
        # Round-trip through the store.
        oid_branch = write_observation(conn, obs_branch)
        obs_branch_round = read_observation(conn, oid_branch)
        eq, diff = _observations_equal(obs_branch, obs_branch_round)
        assert eq, f"branch round-trip failed: {diff}"
        print(f"  OK — branched at position {branch_position}, "
              f"forced token_id={branch_alt_id} (parent's rank-2 at that step)")

        # === 8: query helpers ===
        print("\n[8] Query observations...")
        all_oids = list(query_observations(conn))
        budget_oids = list(query_observations(conn, terminal_event="budget_cap"))
        nonexistent = list(query_observations(conn, terminal_event="nope"))
        print(f"  all={len(all_oids)} terminal=budget_cap={len(budget_oids)} "
              f"terminal=nope={len(nonexistent)}")
        assert len(all_oids) == len(budget_oids) > 0
        assert nonexistent == []
        print("  OK")

        conn.close()

    print("\nALL OK")


if __name__ == "__main__":
    main()
