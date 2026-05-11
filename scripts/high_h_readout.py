"""High-H readout — what was the model attending to, where?

Read-only over `data/peirce.db`. For each of the 100 fp16 trajectories,
in the deep window [DEEP_START, end), pick the top-N highest-entropy
positions and dump for each:

  (absolute position, H, gap, chosen token, alt token, alt_prob,
   plus a few tokens of context on each side).

This is the descriptive half of the slot-readout experiment: at attractors
whose internal H structure carries slot positions, the alt distribution
at those slots reads out the model's prior over the slot's implicit
class. At pinned attractors (no slot structure) the top-H positions are
noise floor and the readout is empty.

Trajectories are printed in descending `osc_amp` (deep-window std H)
order, so high-amplitude / candidate-slot-structure specimens come first;
pinned cycles trail at the bottom. Each trajectory's header tags it
STRUCTURED when its top-H value clears 0.10 nats and PINNED otherwise —
a rough cut-off that mirrors the H<0.1 onset threshold used elsewhere.

Read-only renderer: no model load, no inference. Tokenizer-free.
Run via: uv run python scripts/high_h_readout.py
"""
from __future__ import annotations

import numpy as np

from peirce.runner import default_store_path
from peirce.store import open_store, read_trajectory


DEEP_START = 1024
TOP_N = 5
CONTEXT_LEFT = 6
CONTEXT_RIGHT = 6
STRUCTURED_THRESHOLD = 0.10  # top_H above this counts as "real slot structure"


def render_token(t: str) -> str:
    return t.replace("\n", "\\n").replace("\t", "\\t")


def main() -> None:
    conn = open_store(default_store_path())
    trajectory_ids = [
        tid for (tid,) in conn.execute(
            "SELECT trajectory_id FROM trajectories ORDER BY trajectory_id"
        ).fetchall()
    ]

    items: list[dict] = []
    for tid in trajectory_ids:
        traj = read_trajectory(conn, tid)
        steps = traj.steps
        if len(steps) < DEEP_START + 16:
            continue
        deep = steps[DEEP_START:]
        H = np.fromiter((s.entropy for s in deep), dtype=np.float32)
        osc_amp = float(H.std())
        floor_H = float(np.median(H))
        # Indices into `deep` of the top-N positions by H. argsort gives the
        # *N highest entropy* steps regardless of where in the deep window
        # they sit; for cyclical attractors this typically picks all the
        # phase-aligned slot recurrences (which is what we want — same slot
        # type sampled multiple times).
        top_idx = [int(i) for i in np.argsort(-H)[:TOP_N]]
        items.append({
            "tid": tid,
            "osc_amp": osc_amp,
            "floor_H": floor_H,
            "deep": deep,
            "top_idx": top_idx,
        })

    # Sort by osc_amp desc so STRUCTURED specimens come first.
    items.sort(key=lambda x: -x["osc_amp"])

    n_struct = sum(
        1 for it in items
        if it["deep"][max(it["top_idx"])].entropy >= STRUCTURED_THRESHOLD
        and any(it["deep"][i].entropy >= STRUCTURED_THRESHOLD for i in it["top_idx"])
    )

    print(f"trajectories: {len(items)}")
    print(f"deep window: [{DEEP_START}, end)")
    print(f"top-{TOP_N} highest-H positions per trajectory")
    print(f"context: {CONTEXT_LEFT} tokens before / {CONTEXT_RIGHT} after")
    print(f"STRUCTURED = max top-H >= {STRUCTURED_THRESHOLD}; n_structured ≈ {n_struct}/{len(items)}")
    print()

    for it in items:
        tid = it["tid"]
        deep = it["deep"]
        top_idx = it["top_idx"]
        top_H_max = max(deep[i].entropy for i in top_idx)
        tag = "STRUCTURED" if top_H_max >= STRUCTURED_THRESHOLD else "PINNED    "
        print(
            f"[{tag}]  {tid[:8]}  osc_amp={it['osc_amp']:.4f}  "
            f"floor_H={it['floor_H']:.4f}  top_H={top_H_max:.3f}"
        )
        # Print top positions in chronological order so the cycle phase
        # structure is visible at a glance.
        for i in sorted(top_idx):
            abs_pos = DEEP_START + i
            step = deep[i]
            lo = max(0, i - CONTEXT_LEFT)
            left = "".join(render_token(s.token) for s in deep[lo:i])
            right = "".join(render_token(s.token) for s in deep[i + 1: i + 1 + CONTEXT_RIGHT])
            print(
                f"   pos={abs_pos:5d}  H={step.entropy:.3f}  gap={step.logit_gap:.2f}  "
                f"...{left!r:>40} ⟨chosen={render_token(step.token)!r} | "
                f"alt={render_token(step.alt_token)!r} p={step.alt_prob:.3f}⟩ {right!r}..."
            )
        print()

    conn.close()


if __name__ == "__main__":
    main()
