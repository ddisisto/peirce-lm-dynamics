"""Matplotlib renderings of the persisted full-depth substrate.

Read-only over `data/peirce.db`. Loads the 100 fp16 selection-bias
observations (predicate set: eos + basin_capture(K=4, cycle_window=256,
max_period=32) + window_cap), each backed by a trajectory extended to
L_arch=2047 by full_depth_extension. The v1 terminal-event split
(candidate-basin vs window_cap) is *not* used as a population axis here
— per the depth-collapse finding, that split tracks where the v1
predicate happened to fire, not anything intrinsic to the trajectories
themselves. The shape of collapse is what the data does carry, and it
is what these plots try to surface.

Per-trajectory shape metrics, all population-blind:

- **onset** — first position where smoothed entropy holds below
  ONSET_THRESHOLD=0.1 for ONSET_SMOOTHING=8 consecutive steps.
  "How fast does the entropy drop to the floor?"
- **floor_H** — median entropy over the deep window [DEEP_START, end).
  "Where does the floor sit when collapse has happened?"
- **floor_gap** — median logit_gap over the same window. The model's
  per-step commitment at depth.
- **osc_amp** — std of entropy over the deep window. "How much does
  the trajectory rattle around its floor?" Tight token-cycles have
  ~zero amplitude; phrase-cycles oscillate with amplitude up to ~1.
- **period** — dominant period from autocorrelation of the
  mean-subtracted deep-window entropy, or None when amplitude is below
  noise / no peak is significant.
- **gap_over_H** — floor_gap / max(floor_H, eps). A "commitment ratio":
  how much logit margin per nat of residual uncertainty. Spans many
  orders of magnitude across the population.

Produces four figures under `data/plots/`:

1. `trajectories_aggregate.png` — entropy and logit_gap traces colored
   by onset position; per-position percentile envelopes; per-step
   (entropy, logit_gap) hex density across all 100×~2047 = ~205k steps;
   per-trajectory deep-window (floor_H, floor_gap) scatter.
2. `trajectories_shape.png` — per-trajectory shape-metric distributions
   and pairwise scatters: onset × floor_H × osc_amp × period.
3. `trajectories_outliers.png` — individual entropy + logit_gap traces
   for specimens at named extremes of the shape-metric space, with
   the last 200 chars of generated text annotated.
4. `trajectories_grid.png` — 10×10 small-multiples of smoothed entropy
   traces, sorted by onset position, colored by oscillation amplitude.

Read-only renderer: no model load, no inference. Tokenizer-free.
Run via: uv run python scripts/plot_trajectories.py
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
from matplotlib import cm

from peirce.runner import default_store_path
from peirce.shape import (
    DEEP_START,
    ONSET_SMOOTHING,
    ONSET_THRESHOLD,
    dominant_period,
    entropy_onset,
)
from peirce.store import open_store, read_observation


# Predicate signature that identifies the canonical fp16 selection-bias run.
SELBIAS_PRED_NAMES = {"eos", "basin_capture", "window_cap"}
SELBIAS_BASIN_PARAMS = {"max_period": 32, "cycle_window": 256, "min_repetitions": 4}

SMOOTH_WINDOW = 16

OUT_DIR = Path("data/plots")


@dataclass(frozen=True)
class Specimen:
    oid: str
    entropy: np.ndarray   # (n_pos,)
    logit_gap: np.ndarray
    tokens: str
    observed_length: int  # v1 truncation marker (kept for annotation only)
    onset: int | None
    floor_H: float
    floor_gap: float
    osc_amp: float
    period: int | None
    gap_over_H: float


def is_selection_bias_obs(predicates_json: str) -> bool:
    preds = json.loads(predicates_json)
    names = {p["name"] for p in preds}
    if names != SELBIAS_PRED_NAMES:
        return False
    for p in preds:
        if p["name"] == "basin_capture" and p["params"] != SELBIAS_BASIN_PARAMS:
            return False
    return True


def smooth(x: np.ndarray, window: int = SMOOTH_WINDOW) -> np.ndarray:
    if window <= 1:
        return x
    kernel = np.ones(window, dtype=np.float32) / window
    return np.convolve(x, kernel, mode="same")


def stack_aligned(arrays: list[np.ndarray]) -> np.ndarray:
    """Stack 1-D arrays into (n, max_len), padding with NaN."""
    if not arrays:
        return np.empty((0, 0), dtype=np.float32)
    max_len = max(a.shape[0] for a in arrays)
    out = np.full((len(arrays), max_len), np.nan, dtype=np.float32)
    for i, a in enumerate(arrays):
        out[i, : a.shape[0]] = a
    return out


def preview_text(text: str, width: int) -> str:
    rendered = text.replace("\n", "\\n").replace("\t", "\\t")
    if len(rendered) > width:
        rendered = rendered[: width - 3] + "..."
    return rendered


def load_specimens() -> list[Specimen]:
    conn = open_store(default_store_path())
    rows = conn.execute(
        "SELECT observation_id, predicates_json, terminal_event, observed_length FROM observations"
    ).fetchall()

    specimens: list[Specimen] = []
    for oid, preds_json, _terminal, observed_length in rows:
        if not is_selection_bias_obs(preds_json):
            continue
        obs = read_observation(conn, oid)
        steps = obs.trajectory.steps
        if len(steps) < DEEP_START + 16:
            # need a deep window to characterise; substrate is full-depth so
            # this should not fire, but guard anyway.
            continue
        entropy = np.fromiter((s.entropy for s in steps), dtype=np.float32)
        gap = np.fromiter((s.logit_gap for s in steps), dtype=np.float32)
        tokens = "".join(s.token for s in steps)
        onset = entropy_onset(entropy)
        deep_H = entropy[DEEP_START:]
        deep_G = gap[DEEP_START:]
        floor_H = float(np.median(deep_H))
        floor_gap = float(np.median(deep_G))
        osc_amp = float(np.std(deep_H))
        period = dominant_period(deep_H)
        gap_over_H = floor_gap / max(floor_H, 1e-4)
        specimens.append(Specimen(
            oid=oid,
            entropy=entropy,
            logit_gap=gap,
            tokens=tokens,
            observed_length=observed_length,
            onset=onset,
            floor_H=floor_H,
            floor_gap=floor_gap,
            osc_amp=osc_amp,
            period=period,
            gap_over_H=gap_over_H,
        ))
    conn.close()
    return specimens


# ---------------------------------------------------------------------------
# Figure 1: aggregate views, population-blind, colored continuously by onset.
# ---------------------------------------------------------------------------

def _onset_norm(specimens: list[Specimen]) -> tuple[mcolors.Normalize, np.ndarray]:
    """Onset values for color mapping; never-onset specimens take the high end."""
    onsets_for_color = np.array(
        [s.onset if s.onset is not None else 2048 for s in specimens],
        dtype=np.float32,
    )
    norm = mcolors.Normalize(vmin=0, vmax=2048)
    return norm, onsets_for_color


def fig_aggregate(specimens: list[Specimen], out_path: Path) -> None:
    fig, axes = plt.subplots(3, 2, figsize=(14, 13), constrained_layout=True)
    fig.suptitle(
        "fp16 top-100-from-BOS substrate — full-depth (L_arch=2047), population-blind\n"
        "no v1 / predicate split: shape of collapse is the unit",
        fontsize=12,
    )

    norm, onsets_color = _onset_norm(specimens)
    cmap = cm.viridis

    # --- (A) entropy traces, colored by onset --------------------------------
    ax = axes[0, 0]
    for s, oc in zip(specimens, onsets_color):
        ax.plot(np.arange(s.entropy.size), s.entropy,
                color=cmap(norm(oc)), alpha=0.20, linewidth=0.5)
    stack = stack_aligned([s.entropy for s in specimens])
    p50 = np.nanpercentile(stack, 50, axis=0)
    ax.plot(np.arange(p50.size), p50, color="black", linewidth=1.4, label="population median")
    ax.axhline(ONSET_THRESHOLD, color="grey", linestyle=":", linewidth=0.8,
               label=f"onset threshold = {ONSET_THRESHOLD}")
    ax.set_xlabel("position")
    ax.set_ylabel("entropy (nats)")
    ax.set_title("(A) per-step entropy — color = entropy-onset position (viridis: early→dark)")
    ax.set_ylim(-0.05, 5.0)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)

    # --- (B) entropy percentile envelope -------------------------------------
    ax = axes[0, 1]
    p10, p25, p50, p75, p90 = (
        np.nanpercentile(stack, q, axis=0) for q in (10, 25, 50, 75, 90)
    )
    x = np.arange(p50.size)
    ax.fill_between(x, p10, p90, color="#4c72b0", alpha=0.18, label="p10–p90")
    ax.fill_between(x, p25, p75, color="#4c72b0", alpha=0.35, label="p25–p75 (IQR)")
    ax.plot(x, p50, color="#274060", linewidth=1.4, label="median")
    ax.axhline(ONSET_THRESHOLD, color="grey", linestyle=":", linewidth=0.8)
    ax.set_xlabel("position")
    ax.set_ylabel("entropy (nats)")
    ax.set_title("(B) entropy percentile envelope, single population")
    ax.set_ylim(-0.05, 3.0)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)

    # --- (C) logit_gap traces, colored by onset ------------------------------
    ax = axes[1, 0]
    for s, oc in zip(specimens, onsets_color):
        ax.plot(np.arange(s.logit_gap.size), s.logit_gap,
                color=cmap(norm(oc)), alpha=0.20, linewidth=0.5)
    stack_g = stack_aligned([s.logit_gap for s in specimens])
    p50g = np.nanpercentile(stack_g, 50, axis=0)
    ax.plot(np.arange(p50g.size), p50g, color="black", linewidth=1.4, label="population median")
    ax.set_xlabel("position")
    ax.set_ylabel("logit gap (rank-1 minus rank-2)")
    ax.set_title("(C) per-step logit gap — color = onset position")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(True, alpha=0.3)

    # --- (D) logit_gap percentile envelope -----------------------------------
    ax = axes[1, 1]
    p10g, p25g, p75g, p90g = (
        np.nanpercentile(stack_g, q, axis=0) for q in (10, 25, 75, 90)
    )
    ax.fill_between(x, p10g, p90g, color="#c44e52", alpha=0.18, label="p10–p90")
    ax.fill_between(x, p25g, p75g, color="#c44e52", alpha=0.35, label="p25–p75 (IQR)")
    ax.plot(x, p50g, color="#6e2a2c", linewidth=1.4, label="median")
    ax.set_xlabel("position")
    ax.set_ylabel("logit gap")
    ax.set_title("(D) logit-gap percentile envelope, single population")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(True, alpha=0.3)

    # --- (E) (H, gap) hex density across all per-step pairs ------------------
    ax = axes[2, 0]
    all_H = np.concatenate([s.entropy for s in specimens])
    all_G = np.concatenate([s.logit_gap for s in specimens])
    hb = ax.hexbin(all_H, all_G, gridsize=60, cmap="magma", mincnt=1, bins="log")
    cb = fig.colorbar(hb, ax=ax)
    cb.set_label("log10(count)")
    ax.set_xlabel("entropy (nats)")
    ax.set_ylabel("logit gap")
    ax.set_title(
        f"(E) per-step (H, gap) density across all {len(specimens)}×{stack.shape[1]} steps\n"
        "the L-shape: collapsed states pile in the bottom-right corner"
    )
    ax.grid(True, alpha=0.3)

    # --- (F) per-trajectory deep-window (floor_H, floor_gap) scatter ---------
    ax = axes[2, 1]
    fH = np.array([s.floor_H for s in specimens])
    fG = np.array([s.floor_gap for s in specimens])
    osc = np.array([s.osc_amp for s in specimens])
    sc = ax.scatter(fH, fG, c=osc, cmap="plasma", s=40, edgecolor="white",
                    linewidth=0.4, norm=mcolors.LogNorm(vmin=max(osc.min(), 1e-4),
                                                         vmax=max(osc.max(), 1e-3)))
    cb = fig.colorbar(sc, ax=ax)
    cb.set_label("oscillation amplitude (std H, deep window) [log]")
    ax.set_xscale("log")
    ax.set_xlabel(f"floor entropy: median H over [{DEEP_START}, end) [log]")
    ax.set_ylabel(f"floor logit gap: median over [{DEEP_START}, end)")
    ax.set_title("(F) per-trajectory deep-window (floor_H, floor_gap), color = oscillation")
    ax.grid(True, alpha=0.3, which="both")

    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    print(f"Wrote {out_path}")


# ---------------------------------------------------------------------------
# Figure 2: shape-metric distributions and pairwise scatter — the seams.
# ---------------------------------------------------------------------------

def fig_shape(specimens: list[Specimen], out_path: Path) -> None:
    fig, axes = plt.subplots(3, 2, figsize=(14, 13), constrained_layout=True)
    fig.suptitle(
        "Per-trajectory shape metrics (population-blind, n=100)\n"
        f"deep window = [{DEEP_START}, end); seams: collapse speed × floor depth × oscillation × period",
        fontsize=12,
    )

    onsets = np.array(
        [s.onset if s.onset is not None else 2048 for s in specimens], dtype=np.float32
    )
    onset_finite = np.array([s.onset for s in specimens if s.onset is not None])
    floors = np.array([s.floor_H for s in specimens])
    floor_gaps = np.array([s.floor_gap for s in specimens])
    osc = np.array([s.osc_amp for s in specimens])
    periods_finite = np.array([s.period for s in specimens if s.period is not None])
    gap_over_H = np.array([s.gap_over_H for s in specimens])

    n_never_onset = sum(1 for s in specimens if s.onset is None)
    n_no_period = sum(1 for s in specimens if s.period is None)

    # --- (A) onset distribution (collapse speed) -----------------------------
    ax = axes[0, 0]
    bins = np.linspace(0, 2050, 42)
    ax.hist(onset_finite, bins=bins, color="#4c72b0", alpha=0.75,
            edgecolor="white", linewidth=0.5)
    ax.set_xlabel(
        f"onset position (first {ONSET_SMOOTHING}-step run below H={ONSET_THRESHOLD})"
    )
    ax.set_ylabel("count")
    ax.set_title(
        f"(A) collapse-speed distribution (never-onset: {n_never_onset}/{len(specimens)})"
    )
    ax.grid(True, alpha=0.3)

    # --- (B) oscillation amplitude distribution ------------------------------
    ax = axes[0, 1]
    # log scale because amplitudes span orders of magnitude
    log_osc = np.log10(np.maximum(osc, 1e-5))
    ax.hist(log_osc, bins=30, color="#c44e52", alpha=0.75, edgecolor="white", linewidth=0.5)
    ax.set_xlabel("log10(oscillation amplitude: std of H over deep window)")
    ax.set_ylabel("count")
    ax.set_title("(B) oscillation amplitude — three or so modes visible")
    ax.grid(True, alpha=0.3)

    # --- (C) dominant period distribution ------------------------------------
    ax = axes[1, 0]
    if periods_finite.size > 0:
        ax.hist(periods_finite, bins=np.arange(1, 130, 1), color="#55a868", alpha=0.85,
                edgecolor="white", linewidth=0.4)
    ax.set_xlabel("dominant period (lag of first autocorrelation peak ≥0.3)")
    ax.set_ylabel("count")
    ax.set_title(
        f"(C) period at the floor "
        f"(no-period: {n_no_period}/{len(specimens)} — variance below noise)"
    )
    ax.grid(True, alpha=0.3)

    # --- (D) onset × floor_H, color by oscillation ---------------------------
    ax = axes[1, 1]
    sc = ax.scatter(onsets, np.maximum(floors, 1e-4), c=osc, cmap="plasma", s=40,
                    edgecolor="white", linewidth=0.4,
                    norm=mcolors.LogNorm(vmin=max(osc.min(), 1e-4),
                                          vmax=max(osc.max(), 1e-3)))
    cb = fig.colorbar(sc, ax=ax)
    cb.set_label("oscillation amplitude [log]")
    ax.set_yscale("log")
    ax.set_xlabel("onset position (collapse speed; never-onset → 2048)")
    ax.set_ylabel("floor H [log]")
    ax.set_title("(D) collapse speed × floor depth, colored by oscillation")
    ax.grid(True, alpha=0.3, which="both")

    # --- (E) floor_H × floor_gap, color by oscillation -----------------------
    ax = axes[2, 0]
    sc = ax.scatter(np.maximum(floors, 1e-4), floor_gaps, c=osc, cmap="plasma", s=40,
                    edgecolor="white", linewidth=0.4,
                    norm=mcolors.LogNorm(vmin=max(osc.min(), 1e-4),
                                          vmax=max(osc.max(), 1e-3)))
    cb = fig.colorbar(sc, ax=ax)
    cb.set_label("oscillation amplitude [log]")
    ax.set_xscale("log")
    ax.set_xlabel("floor H [log]")
    ax.set_ylabel("floor logit gap")
    ax.set_title("(E) the (H, gap) relationship, per-trajectory at depth")
    ax.grid(True, alpha=0.3, which="both")

    # --- (F) gap-over-H ratio distribution -----------------------------------
    ax = axes[2, 1]
    log_ratio = np.log10(np.maximum(gap_over_H, 1e-3))
    ax.hist(log_ratio, bins=30, color="#8172b3", alpha=0.85, edgecolor="white", linewidth=0.4)
    ax.set_xlabel("log10(floor logit gap / floor entropy)")
    ax.set_ylabel("count")
    ax.set_title(
        "(F) commitment ratio at the floor — how much margin per nat of slack"
    )
    ax.grid(True, alpha=0.3)

    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    print(f"Wrote {out_path}")


# ---------------------------------------------------------------------------
# Figure 3: outliers — specimens at named extremes of the shape-metric space.
# ---------------------------------------------------------------------------

def fig_outliers(specimens: list[Specimen], out_path: Path) -> None:
    has_onset = [s for s in specimens if s.onset is not None]
    has_period = [s for s in specimens if s.period is not None]

    selected: list[tuple[Specimen, str]] = []

    if has_onset:
        s_fast = min(has_onset, key=lambda s: s.onset)  # type: ignore[arg-type]
        s_slow = max(has_onset, key=lambda s: s.onset)  # type: ignore[arg-type]
        selected.append((s_fast, f"fastest collapse  (onset={s_fast.onset})"))
        selected.append((s_slow, f"slowest collapse  (onset={s_slow.onset})"))

    s_loosest = max(specimens, key=lambda s: s.osc_amp)
    s_tightest = min(specimens, key=lambda s: s.osc_amp)
    selected.append((s_loosest, f"loosest floor      (osc_amp={s_loosest.osc_amp:.3f})"))
    selected.append((s_tightest, f"tightest floor     (osc_amp={s_tightest.osc_amp:.3g})"))

    if has_period:
        s_long = max(has_period, key=lambda s: s.period)  # type: ignore[arg-type]
        s_short = min(has_period, key=lambda s: s.period)  # type: ignore[arg-type]
        selected.append((s_long, f"longest period     (period={s_long.period}, amp={s_long.osc_amp:.3f})"))
        selected.append((s_short, f"shortest period    (period={s_short.period}, amp={s_short.osc_amp:.3f})"))

    s_lowR = min(specimens, key=lambda s: s.gap_over_H)
    s_highR = max(specimens, key=lambda s: s.gap_over_H)
    selected.append((s_lowR,  f"lowest gap/H ratio  (ratio={s_lowR.gap_over_H:.1f})"))
    selected.append((s_highR, f"highest gap/H ratio (ratio={s_highR.gap_over_H:.0f})"))

    # Deduplicate while preserving order (a single specimen may win multiple labels).
    seen: set[str] = set()
    unique: list[tuple[Specimen, str]] = []
    for s, lbl in selected:
        key = s.oid
        if key in seen:
            unique[-1] = (unique[-1][0], unique[-1][1] + " · " + lbl)
            # if the duplicate is non-adjacent we still want to merge:
            for i, (s_existing, lbl_existing) in enumerate(unique):
                if s_existing.oid == key:
                    unique[i] = (s_existing,
                                 lbl_existing if lbl in lbl_existing
                                 else lbl_existing + " · " + lbl)
                    break
        else:
            seen.add(key)
            unique.append((s, lbl))

    n = len(unique)
    fig, axes = plt.subplots(n, 1, figsize=(14, max(2.0 * n, 4.0)),
                             sharex=True, constrained_layout=True)
    if n == 1:
        axes = [axes]
    fig.suptitle(
        "Individual specimens at named extremes of the shape-metric space\n"
        "blue = entropy (smoothed), red = logit_gap (smoothed); "
        "vertical dotted = entropy-onset; smoothing window=16",
        fontsize=11,
    )

    for ax, (s, label) in zip(axes, unique):
        e = s.entropy
        g = s.logit_gap
        x = np.arange(e.size)
        ax.plot(x, e, color="#1f77b4", alpha=0.25, linewidth=0.5)
        ax.plot(x, smooth(e), color="#1f77b4", linewidth=1.2)
        ax.set_ylabel("H", color="#1f77b4")
        ax.tick_params(axis="y", labelcolor="#1f77b4")
        ax.set_ylim(-0.1, max(3.0, float(e.max()) + 0.2))
        ax.axhline(ONSET_THRESHOLD, color="grey", linestyle=":", linewidth=0.6)

        ax2 = ax.twinx()
        ax2.plot(x, g, color="#d62728", alpha=0.25, linewidth=0.5)
        ax2.plot(x, smooth(g), color="#d62728", linewidth=1.2)
        ax2.set_ylabel("gap", color="#d62728")
        ax2.tick_params(axis="y", labelcolor="#d62728")

        if s.onset is not None:
            ax.axvline(s.onset, color="grey", linestyle=":", linewidth=0.8, alpha=0.7)

        tail = preview_text(s.tokens[-300:], 200)
        ax.set_title(
            f"{label}  —  {s.oid[:8]}  "
            f"[floor_H={s.floor_H:.3f}, floor_gap={s.floor_gap:.2f}, "
            f"period={s.period}, gap/H={s.gap_over_H:.1f}]\n"
            f"tail: {tail}",
            fontsize=8, loc="left",
        )
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel("position")
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    print(f"Wrote {out_path}")


# ---------------------------------------------------------------------------
# Figure 4: small-multiples grid, sorted by onset, colored by oscillation.
# ---------------------------------------------------------------------------

def fig_grid(specimens: list[Specimen], out_path: Path) -> None:
    def sort_key(s: Specimen) -> float:
        return float("inf") if s.onset is None else float(s.onset)

    ordered = sorted(specimens, key=sort_key)
    osc_arr = np.array([s.osc_amp for s in ordered])
    norm = mcolors.LogNorm(vmin=max(osc_arr.min(), 1e-5),
                            vmax=max(osc_arr.max(), 1e-3))
    cmap = cm.plasma

    n = len(ordered)
    cols = 10
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 1.7, rows * 1.1),
                             sharex=True, sharey=True, constrained_layout=True)
    fig.suptitle(
        "Small-multiples: per-trajectory entropy trace (smoothed)\n"
        f"sorted by entropy-onset position; line color = oscillation amplitude (log); n={n}",
        fontsize=11,
    )

    axes_flat = axes.flatten()
    for ax in axes_flat:
        ax.set_axis_off()

    for ax, s in zip(axes_flat, ordered):
        ax.set_axis_on()
        e = s.entropy
        x = np.arange(e.size)
        ax.plot(x, smooth(e), color=cmap(norm(s.osc_amp)), linewidth=0.8)
        ax.axhline(ONSET_THRESHOLD, color="grey", linestyle=":", linewidth=0.4)
        if s.onset is not None:
            ax.axvline(s.onset, color="grey", linestyle=":", linewidth=0.4)
        ax.set_ylim(-0.05, 3.0)
        ax.set_xlim(0, 2050)
        ax.tick_params(labelsize=5)
        title = s.oid[:6]
        if s.period is not None:
            title += f"  T={s.period}"
        ax.set_title(title, fontsize=6)

    # Add a colorbar for oscillation amplitude.
    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=axes_flat, location="right", shrink=0.6, pad=0.02)
    cbar.set_label("oscillation amplitude (std H, deep window) [log]", fontsize=8)

    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    print(f"Wrote {out_path}")


# ---------------------------------------------------------------------------

def main() -> None:
    print(f"Store: {default_store_path()}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    specimens = load_specimens()
    print(f"Selection-bias observations loaded: {len(specimens)}")
    print(f"  never-onset (entropy never holds below {ONSET_THRESHOLD} for "
          f"{ONSET_SMOOTHING} steps): {sum(1 for s in specimens if s.onset is None)}")
    print(f"  no-period (deep-window variance too low or no peak): "
          f"{sum(1 for s in specimens if s.period is None)}")
    onsets = [s.onset for s in specimens if s.onset is not None]
    if onsets:
        print(
            f"  onset stats: min={min(onsets)} median={int(np.median(onsets))} "
            f"max={max(onsets)}"
        )
    floors = [s.floor_H for s in specimens]
    print(f"  floor_H stats: min={min(floors):.4f} median={float(np.median(floors)):.4f} "
          f"max={max(floors):.4f}")

    fig_aggregate(specimens, OUT_DIR / "trajectories_aggregate.png")
    fig_shape(specimens, OUT_DIR / "trajectories_shape.png")
    fig_outliers(specimens, OUT_DIR / "trajectories_outliers.png")
    fig_grid(specimens, OUT_DIR / "trajectories_grid.png")


if __name__ == "__main__":
    main()
