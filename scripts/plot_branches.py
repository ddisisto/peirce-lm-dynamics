"""Matplotlib companion to `branch_compare.py`.

Per-pair three-panel figures (entropy / logit_gap / gap-over-H overlays of
parent vs branch, with the branch position marked) plus grid figures tiling
H-trace overlays by outcome and (when the first-batch manifest is importable)
by regime tag. The branch position is the event of interest; the time axis
is `[max(0, branch_position - 200), len(parent))` so post-branch evolution
is shown in full and 200 steps of pre-branch context are visible. No outcome-
based colouring of the branch line — the eye reads the category, not the
classifier's already-applied label.

Read-only over the store; no model load, no inference. Writes under
`data/plots/branches/`.

Run via: uv run python scripts/plot_branches.py
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# co-located scripts; ensure import resolution under `uv run`
sys.path.insert(0, str(Path(__file__).resolve().parent))

from branch_compare import compare_pair, find_branches
from peirce.runner import default_store_path
from peirce.store import open_store, read_trajectory

try:
    from first_batch_branches import BATCH as _FIRST_BATCH
    REGIME_TAG_BY_PREFIX = {prefix: tag for prefix, tag in _FIRST_BATCH}
except Exception:
    REGIME_TAG_BY_PREFIX = {}

PLOTS_DIR = Path(__file__).resolve().parent.parent / "data" / "plots" / "branches"
WINDOW_BEFORE = 200
GAP_OVER_H_EPS = 1e-4

PARENT_COLOR = "#888888"   # muted grey baseline
BRANCH_COLOR = "#1f77b4"   # matplotlib default blue
DIV_COLOR = "#cc0000"      # divergence rule


def _window(L, branch_position):
    return max(0, branch_position - WINDOW_BEFORE), L


def _series(steps, lo, hi):
    H = np.array([s.entropy for s in steps[lo:hi]], dtype=np.float64)
    gap = np.array([s.logit_gap for s in steps[lo:hi]], dtype=np.float64)
    goH = gap / np.maximum(H, GAP_OVER_H_EPS)
    return H, gap, goH


def _pair_title(pair, tag):
    return (
        f"{pair['parent_tid'][:8]} → {pair['branch_tid'][:8]}  [{tag}]  "
        f"pos={pair['branch_position']}  alt={pair['alt_token']!r}  "
        f"T_req={pair['T_req']:.2f}  outcome={pair['outcome']}"
    )


def plot_pair(parent_steps, branch_steps, pair, tag, out_path):
    bp = pair["branch_position"]
    lo, hi = _window(len(parent_steps), bp)
    xs = np.arange(lo, hi)
    p_H, p_g, p_goH = _series(parent_steps, lo, hi)
    b_H, b_g, b_goH = _series(branch_steps, lo, hi)

    fig, axes = plt.subplots(3, 1, figsize=(12, 7), sharex=True)
    axes[0].plot(xs, p_H, color=PARENT_COLOR, lw=0.8, label="parent")
    axes[0].plot(xs, b_H, color=BRANCH_COLOR, lw=0.8, label="branch")
    axes[0].axvline(bp, color=DIV_COLOR, lw=0.8, ls="--")
    axes[0].set_ylabel("entropy")
    axes[0].legend(loc="upper right", fontsize=8)
    axes[0].set_title(_pair_title(pair, tag), fontsize=9)

    axes[1].plot(xs, p_g, color=PARENT_COLOR, lw=0.8)
    axes[1].plot(xs, b_g, color=BRANCH_COLOR, lw=0.8)
    axes[1].axvline(bp, color=DIV_COLOR, lw=0.8, ls="--")
    axes[1].set_ylabel("logit_gap")

    axes[2].plot(xs, p_goH, color=PARENT_COLOR, lw=0.8)
    axes[2].plot(xs, b_goH, color=BRANCH_COLOR, lw=0.8)
    axes[2].axvline(bp, color=DIV_COLOR, lw=0.8, ls="--")
    axes[2].set_ylabel("gap / H")
    axes[2].set_xlabel("position")

    fig.tight_layout()
    fig.savefig(out_path, dpi=100)
    plt.close(fig)


def plot_grid(items, group_label, out_path):
    """H-trace overlay tiles. `items` is a list of (parent_steps, branch_steps, pair, tag)."""
    n = len(items)
    if n == 0:
        return
    ncols = min(3, n)
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.5 * ncols, 2.3 * nrows), squeeze=False)
    for i, (p_steps, b_steps, pair, tag) in enumerate(items):
        ax = axes[i // ncols][i % ncols]
        bp = pair["branch_position"]
        lo, hi = _window(len(p_steps), bp)
        xs = np.arange(lo, hi)
        p_H, _, _ = _series(p_steps, lo, hi)
        b_H, _, _ = _series(b_steps, lo, hi)
        ax.plot(xs, p_H, color=PARENT_COLOR, lw=0.6)
        ax.plot(xs, b_H, color=BRANCH_COLOR, lw=0.6)
        ax.axvline(bp, color=DIV_COLOR, lw=0.6, ls="--")
        ax.set_title(
            f"{pair['parent_tid'][:8]}→{pair['branch_tid'][:8]} [{tag}]  "
            f"T={pair['T_req']:.2f}  {pair['outcome']}",
            fontsize=7,
        )
        ax.tick_params(labelsize=6)
    for j in range(n, nrows * ncols):
        axes[j // ncols][j % ncols].axis("off")
    fig.suptitle(f"branch pairs — {group_label}", fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, dpi=100)
    plt.close(fig)


def main():
    conn = open_store(default_store_path())
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    branches_by_parent = find_branches(conn)
    n_branches = sum(len(b) for b in branches_by_parent.values())
    print(f"Plotting {n_branches} branch pair(s); outdir: {PLOTS_DIR}")
    print(f"Window: [max(0, branch_position - {WINDOW_BEFORE}), len(parent))")
    if REGIME_TAG_BY_PREFIX:
        print(f"Regime-tag manifest: first_batch_branches.BATCH ({len(REGIME_TAG_BY_PREFIX)} entries)")
    else:
        print("Regime-tag manifest: unavailable; grid_by_regime skipped")
    print()

    cache = {}

    def get_traj(tid):
        if tid not in cache:
            cache[tid] = read_trajectory(conn, tid)
        return cache[tid]

    by_outcome = defaultdict(list)
    by_regime = defaultdict(list)
    written = 0

    for parent_tid in sorted(branches_by_parent.keys()):
        parent = get_traj(parent_tid)
        for branch_tid, last_inj in branches_by_parent[parent_tid]:
            bp = last_inj[0]
            branch = get_traj(branch_tid)
            pair = compare_pair(conn, parent_tid, branch_tid, bp)
            tag = REGIME_TAG_BY_PREFIX.get(parent_tid[:8], "UNKNOWN")

            out_path = PLOTS_DIR / f"{parent_tid[:8]}__{branch_tid[:8]}.png"
            plot_pair(parent.steps, branch.steps, pair, tag, out_path)
            written += 1

            item = (parent.steps, branch.steps, pair, tag)
            by_outcome[pair["outcome"]].append(item)
            by_regime[tag].append(item)

    for outcome, items in by_outcome.items():
        out = PLOTS_DIR / f"grid_outcome_{outcome.replace('-', '_')}.png"
        plot_grid(items, f"outcome = {outcome}", out)

    if REGIME_TAG_BY_PREFIX:
        for tag, items in by_regime.items():
            slug = tag.lower().replace("-", "_")
            out = PLOTS_DIR / f"grid_regime_{slug}.png"
            plot_grid(items, f"regime = {tag}", out)

    msg = f"Wrote {written} per-pair figures + {len(by_outcome)} outcome grids"
    if REGIME_TAG_BY_PREFIX:
        msg += f" + {len(by_regime)} regime grids"
    print(msg)


if __name__ == "__main__":
    main()
