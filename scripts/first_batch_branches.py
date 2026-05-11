"""C2 first-batch branches: alternate-path continuation over observations.md exemplars.

Twenty-five branches across the trajectory_ids surfaced in `observations.md`
across the three Cycle-2 entries (N1 first-light, N1.5 catalog, NOPERIOD audit).
Each branch is produced by perturbing the parent at the deep-window position of
lowest `gap_over_H` (the catalog's principled axis: commitment ratio at the
floor — where the model is most open relative to its entropy) with the
argmax-of-non-chosen alt token persisted at that step.

Uniform selection rule across the batch: the same per-trajectory criterion is
applied regardless of regime tag, so controls (SCAFFOLD, NOPERIOD Cluster A)
get "the most-leverage-able-looking position within them" — the right baseline
question is whether perturbation redirects even there.

Selection rule is deliberately a beginning, not a claim. Per the design-reqs
protocol's two empirical questions (transient leverage; cyclic leverage), this
batch is the first inferential read against the substrate; follow-up batches
will broaden controls and alt-token rules (Gumbel-Top-k second batch).

Runs are persisted under predicates `[eos, window_cap(L_arch)]` — substrate-
aligned. The branch comparison renderer (named in `design-reqs.md`) is the
descriptive companion; design deferred until this batch lands.

Run via: uv run python scripts/first_batch_branches.py
"""
from __future__ import annotations

import time
from collections import Counter

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from peirce.predicates import eos_predicate, window_cap_predicate
from peirce.runner import branch_observe, default_store_path
from peirce.shape import DEEP_START
from peirce.store import open_store, read_trajectory, trajectory_hash

MODEL_ID = "EleutherAI/pythia-1b-deduped"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
GAP_OVER_H_EPS = 1e-4  # matches shape_catalog.py convention

# trajectory_id[:8] prefixes surfaced in observations.md, grouped by regime
# for log readability. Order has no semantic load; uniform selection rule.
BATCH = [
    # SLOTTED-CLASS (textbook class slot)
    ("49ba0b75", "SLOTTED-CLASS"),
    # SLOTTED-COUNTER (4 specimens from N1 table)
    ("13f9cd8d", "SLOTTED-COUNTER-INT"),
    ("d24c9484", "SLOTTED-COUNTER-INT"),
    ("d2562221", "SLOTTED-COUNTER-LETTER"),
    ("1f812a06", "SLOTTED-COUNTER-INT"),
    # Harmonic-period specimens (7 specimens, N1 period-detection-harmonics paragraph)
    ("5f3c1e41", "SLOTTED-HARMONIC"),
    ("9bde3a7a", "SLOTTED-HARMONIC"),
    ("a36f4b57", "SLOTTED-HARMONIC"),
    ("fffba0e8", "SLOTTED-HARMONIC"),
    ("0a52701d", "SLOTTED-HARMONIC"),
    ("a2cfa7d4", "SLOTTED-HARMONIC"),
    ("60e599bd", "SLOTTED-HARMONIC"),
    # SCAFFOLD with commitment-strength heterogeneity / single-mode template cycles
    ("edb2b7cf", "SCAFFOLD"),
    ("8ea1fab2", "SCAFFOLD"),
    ("fa70f050", "SCAFFOLD"),
    ("052ebc5a", "SCAFFOLD"),
    ("4a211c24", "SCAFFOLD"),
    # NOPERIOD Cluster A (honest no-period; memoryless baseline)
    ("9af67bb8", "NOPERIOD-A"),
    ("53e800cb", "NOPERIOD-A"),
    ("5b628579", "NOPERIOD-A"),
    ("7c7228bf", "NOPERIOD-A"),
    ("c82e06a6", "NOPERIOD-A"),
    # NOPERIOD Cluster B (weak quasi-periodic structure on bimodal H; spike candidates)
    ("48a13037", "NOPERIOD-B"),
    ("7c66ed46", "NOPERIOD-B"),
    ("4e26d572", "NOPERIOD-B"),
]


def resolve_prefix(conn, prefix: str) -> str:
    """Resolve an 8-char trajectory_id prefix to the full id. Asserts uniqueness."""
    rows = conn.execute(
        "SELECT trajectory_id FROM trajectories WHERE trajectory_id LIKE ?",
        (f"{prefix}%",),
    ).fetchall()
    if len(rows) == 0:
        raise KeyError(f"no trajectory matching prefix {prefix!r}")
    if len(rows) > 1:
        raise ValueError(
            f"prefix {prefix!r} matched {len(rows)} trajectories — collision"
        )
    return rows[0][0]


def select_branch_position(steps) -> int:
    """Lowest gap_over_H in the deep window [DEEP_START, len(steps))."""
    n = len(steps)
    if n <= DEEP_START:
        raise ValueError(
            f"trajectory has only {n} steps; deep window starts at {DEEP_START}"
        )
    H = np.array([s.entropy for s in steps[DEEP_START:]], dtype=np.float64)
    gap = np.array([s.logit_gap for s in steps[DEEP_START:]], dtype=np.float64)
    gap_over_H = gap / np.maximum(H, GAP_OVER_H_EPS)
    return DEEP_START + int(np.argmin(gap_over_H))


def main() -> None:
    print(f"Loading {MODEL_ID} on {DEVICE}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID).to(DEVICE).eval()

    eos_id = tokenizer.eos_token_id
    L_arch = model.config.max_position_embeddings

    predicates = [
        eos_predicate(eos_id),
        window_cap_predicate(L_arch),
    ]

    store_path = default_store_path()
    store = open_store(store_path)
    print(f"Store: {store_path}")
    print(f"L_arch: {L_arch}  deep_window: [{DEEP_START}, end)  EOS id: {eos_id}")
    print(f"Predicates: [eos, window_cap]  inference: hard_cap_t0")
    print(f"Selection: argmin gap_over_H over deep window; alt = persisted alt_token_id")
    print(f"Batch size: {len(BATCH)}\n")

    n_cached = 0
    n_extended = 0
    terminals: Counter[str] = Counter()

    header = (
        f"  {'idx':>3} {'tag':<22} {'parent':<10} {'pos':>5} "
        f"{'H':>7} {'gap':>7} {'goH':>9} {'alt':<16} "
        f"{'branch':<10} {'term':<11} {'len':>5} {'t(s)':>7}"
    )
    print(header)
    print(f"  {'-' * (len(header) - 2)}")

    t_start = time.perf_counter()
    for i, (prefix, tag) in enumerate(BATCH):
        full_tid = resolve_prefix(store, prefix)
        parent = read_trajectory(store, full_tid)
        pos = select_branch_position(parent.steps)
        parent_step = parent.steps[pos]
        alt_id = parent_step.alt_token_id
        alt_text = parent_step.alt_token
        H = parent_step.entropy
        gap = parent_step.logit_gap
        goH = gap / max(H, GAP_OVER_H_EPS)

        t_obs = time.perf_counter()
        obs = branch_observe(
            store, model, tokenizer,
            parent_trajectory_id=full_tid,
            branch_position=pos,
            alt_token_id=alt_id,
            predicates=predicates,
        )
        elapsed = time.perf_counter() - t_obs
        if elapsed < 0.05:
            n_cached += 1
        else:
            n_extended += 1
        terminals[obs.terminal_event] += 1

        # branch trajectory_id by hash construction over augmented injections
        branch_tid = trajectory_hash(obs.trajectory)

        print(
            f"  {i:>3d} {tag:<22} {prefix:<10} {pos:>5d} "
            f"{H:>7.4f} {gap:>7.3f} {goH:>9.3f} {alt_text!r:<16} "
            f"{branch_tid[:8]:<10} {obs.terminal_event:<11} {obs.length:>5d} "
            f"{elapsed:>7.2f}",
            flush=True,
        )

    t_total = time.perf_counter() - t_start
    print()
    print(f"Total: {t_total:.1f}s  cache={n_cached}  extended={n_extended}")
    print(f"Terminal events: {dict(terminals)}")


if __name__ == "__main__":
    main()
