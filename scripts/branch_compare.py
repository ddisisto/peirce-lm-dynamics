"""Compare branch trajectories to their parents over common axes.

Discovers branch trajectories in the store (any trajectory with `len(injections)
> 1`) and pairs each with its parent (the trajectory whose injections are the
branch's prefix). Per pair, computes a classification of outcome under a
heuristic 3-way rule, plus a sampling-strategy axis via T_req — the temperature
at which the alt-token would have probability 0.1 in a two-token softmax over
(chosen, alt).

Outcome classifier (heuristic, revisable as the empirical surface grows):

- **basin-switch** — parent's period and branch's period differ (one None vs
  one detected, or both detected but unequal); OR peak-acf drops by > 0.20
  while period is preserved (early-divergence weakening case).
- **re-absorbed** — period preserved (or both NOPERIOD), peak-acf preserved,
  and divergence span (last_div - branch_position + 1) <= 2 * period (or <= 100
  for NOPERIOD).
- **wandering** — period and peak-acf preserved, but divergence span exceeds
  the re-absorbed threshold. Same attractor structurally; tokens drift.

T_req axis (sampling-strategy reframing):

  T_req = gap / log(9) ≈ gap / 2.197

is the temperature at which the alt-token would have probability 0.1 under a
two-token softmax over (chosen, alt). The full distribution carries other mass,
so this underestimates the actual T needed for p_alt = 0.1 — but T_req is the
right order-of-magnitude for "would standard sampling at this T realistically
pick the alt?" Buckets: low (≤0.15) ≈ readily sampleable; mid (0.15..2.0);
high (>2.0) ≈ essentially never sampled.

Read-only over the store; no model load, no inference.

Run via: uv run python scripts/branch_compare.py
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict

import numpy as np

from peirce.runner import default_store_path
from peirce.shape import DEEP_START, acf_peaks, dominant_period
from peirce.store import open_store, read_trajectory

LOG9 = float(np.log(9.0))
RE_ABSORBED_NOPERIOD_SPAN = 100  # fallback period_ref for NOPERIOD
PEAK_ACF_DROP_THRESHOLD = 0.20


def find_branches(conn):
    """Discover branch trajectories. Returns dict: parent_tid -> list[(branch_tid, last_injection)]."""
    rows = conn.execute(
        "SELECT trajectory_id, injections_json FROM trajectories"
    ).fetchall()
    inj_by_tid = {}
    for tid, inj_json in rows:
        inj = tuple((i["position"], i["chosen_id"]) for i in json.loads(inj_json))
        inj_by_tid[tid] = inj
    tid_by_inj = {inj: tid for tid, inj in inj_by_tid.items()}

    branches_by_parent = defaultdict(list)
    for tid, inj in inj_by_tid.items():
        if len(inj) < 2:
            continue
        parent_inj = inj[:-1]
        parent_tid = tid_by_inj.get(parent_inj)
        if parent_tid is not None:
            branches_by_parent[parent_tid].append((tid, inj[-1]))
    return branches_by_parent


def deep_shape(steps):
    H = np.array([s.entropy for s in steps[DEEP_START:]], dtype=np.float64)
    peaks = acf_peaks(H)
    return {
        "floor_H": float(np.median(H)),
        "osc_amp": float(np.std(H)),
        "period": dominant_period(H),
        "peak_acf": peaks[0][1] if peaks else None,
    }


def classify_outcome(parent_shape, branch_shape, last_div, branch_position):
    pp, bp = parent_shape["period"], branch_shape["period"]
    div_span = (last_div - branch_position + 1) if last_div is not None else 0

    if (pp is None) != (bp is None):
        return "basin-switch"
    if pp is not None and bp is not None and pp != bp:
        return "basin-switch"
    if parent_shape["peak_acf"] and branch_shape["peak_acf"]:
        if parent_shape["peak_acf"] - branch_shape["peak_acf"] > PEAK_ACF_DROP_THRESHOLD:
            return "basin-switch"

    period_ref = pp if pp else RE_ABSORBED_NOPERIOD_SPAN
    if div_span <= 2 * period_ref:
        return "re-absorbed"
    return "wandering"


def compare_pair(conn, parent_tid, branch_tid, branch_position):
    parent = read_trajectory(conn, parent_tid)
    branch = read_trajectory(conn, branch_tid)
    parent_step = parent.steps[branch_position]
    gap = parent_step.logit_gap

    last_div = None
    for i in range(len(parent.steps) - 1, branch_position - 1, -1):
        if parent.steps[i].token_id != branch.steps[i].token_id:
            last_div = i
            break
    n_diff = sum(
        1 for i in range(branch_position, len(parent.steps))
        if parent.steps[i].token_id != branch.steps[i].token_id
    )
    tail = len(parent.steps) - branch_position

    ps = deep_shape(parent.steps)
    bs = deep_shape(branch.steps)
    outcome = classify_outcome(ps, bs, last_div, branch_position)

    return {
        "parent_tid": parent_tid, "branch_tid": branch_tid,
        "branch_position": branch_position,
        "alt_token": parent_step.alt_token,
        "gap": gap, "H": parent_step.entropy,
        "T_req": gap / LOG9,
        "alt_prob_T1": parent_step.alt_prob,
        "n_diff": n_diff, "tail": tail,
        "div_span": (last_div - branch_position + 1) if last_div is not None else 0,
        "parent_shape": ps,
        "branch_shape": bs,
        "outcome": outcome,
    }


def t_req_bucket(t):
    if t <= 0.15:
        return "low (≤0.15)"
    if t <= 2.0:
        return "mid (0.15..2.0)"
    return "high (>2.0)"


def main():
    conn = open_store(default_store_path())
    branches_by_parent = find_branches(conn)

    n_branches = sum(len(b) for b in branches_by_parent.values())
    print(f"Branches: {n_branches} across {len(branches_by_parent)} parents")
    print(f"DEEP_START={DEEP_START}  T_req: gap / log(9)  [p_alt=0.1, two-token approx]")
    print(f"Classifier: basin-switch on period change or peak_acf drop > {PEAK_ACF_DROP_THRESHOLD}; "
          f"re-absorbed on div_span <= 2*period")
    print()

    pairs = []
    for parent_tid in sorted(branches_by_parent.keys()):
        for branch_tid, _last_inj in branches_by_parent[parent_tid]:
            pos = _last_inj[0]
            pairs.append(compare_pair(conn, parent_tid, branch_tid, pos))
    pairs.sort(key=lambda p: (p["outcome"], -p["T_req"]))

    # === Table 1: sampling axis ===
    print("== Sampling-axis table (sorted by outcome, then -T_req) ==")
    hdr = (f"{'parent':<10} {'branch':<10} {'pos':>5} {'alt':<18} "
           f"{'gap':>7} {'T_req':>7} {'alt p(T=1)':>10} {'outcome':<14}")
    print(hdr)
    print("-" * len(hdr))
    for p in pairs:
        print(f"{p['parent_tid'][:8]:<10} {p['branch_tid'][:8]:<10} {p['branch_position']:>5} "
              f"{p['alt_token']!r:<18} {p['gap']:>7.3f} {p['T_req']:>7.3f} "
              f"{p['alt_prob_T1']:>10.3f} {p['outcome']:<14}")
    print()

    # === Table 2: outcomes ===
    print("== Outcomes table (same order) ==")
    hdr = (f"{'parent':<10} {'branch':<10} {'n_diff/tail':>16} {'div_span':>9} "
           f"{'p_period':>9} {'b_period':>9} {'p_acf':>7} {'b_acf':>7} {'outcome':<14}")
    print(hdr)
    print("-" * len(hdr))
    for p in pairs:
        pp = str(p['parent_shape']['period']) if p['parent_shape']['period'] else "None"
        bp = str(p['branch_shape']['period']) if p['branch_shape']['period'] else "None"
        pa = f"{p['parent_shape']['peak_acf']:.2f}" if p['parent_shape']['peak_acf'] else "—"
        ba = f"{p['branch_shape']['peak_acf']:.2f}" if p['branch_shape']['peak_acf'] else "—"
        diff_pct = 100 * p['n_diff'] / p['tail'] if p['tail'] else 0
        print(f"{p['parent_tid'][:8]:<10} {p['branch_tid'][:8]:<10} "
              f"{p['n_diff']:>4}/{p['tail']:<4} ({diff_pct:>3.0f}%) {p['div_span']:>9} "
              f"{pp:>9} {bp:>9} {pa:>7} {ba:>7} {p['outcome']:<14}")
    print()

    # === Summary ===
    counts = Counter(p["outcome"] for p in pairs)
    print(f"== Outcome distribution ==")
    for k in ["re-absorbed", "wandering", "basin-switch"]:
        print(f"  {k:<14} {counts.get(k, 0):>3}/{len(pairs)}")
    print()

    T_dist = [p["T_req"] for p in pairs]
    print(f"== T_req distribution ==")
    print(f"  min={min(T_dist):.3f}  median={np.median(T_dist):.3f}  max={max(T_dist):.3f}")
    for b in ["low (≤0.15)", "mid (0.15..2.0)", "high (>2.0)"]:
        n = sum(1 for t in T_dist if t_req_bucket(t) == b)
        print(f"  {b:<18} {n}/{len(T_dist)}")
    print()

    xtab = defaultdict(Counter)
    for p in pairs:
        xtab[t_req_bucket(p["T_req"])][p["outcome"]] += 1
    print(f"== T_req × outcome cross-tab ==")
    hdr = f"  {'bucket':<18} {'re-absorbed':>12} {'wandering':>10} {'basin-switch':>13} {'total':>6}"
    print(hdr)
    for b in ["low (≤0.15)", "mid (0.15..2.0)", "high (>2.0)"]:
        c = xtab[b]
        total = sum(c.values())
        print(f"  {b:<18} {c.get('re-absorbed', 0):>12} {c.get('wandering', 0):>10} "
              f"{c.get('basin-switch', 0):>13} {total:>6}")


if __name__ == "__main__":
    main()
