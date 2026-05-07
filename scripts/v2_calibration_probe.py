"""Basin detection v2 — calibration probe (read-only over data/peirce.db).

Pre-design data for the v2 detector design questions named in ROADMAP.md
"basin-v2": (1) detector signal — single statistic, combination, or
multi-feature classifier? (2) basin identity for non-cyclical basins?
(3) runtime cutoff vs post-hoc classification? (4) separator vs basin
within enumerations?

Loads the selection-bias observations from the persisted store
(predicate set: eos + basin_capture(K=4, max_period=32, cycle_window=256)
+ window_cap; inference hard_cap_t0). Two populations:

- **confirmed positive**: 63 trajectories captured by the v1 cycle
  predicate at depth ≤ ~575. Late-window stats reflect *just past*
  capture, not stable-in-basin asymptote — that's the runtime view.
- **candidate positive**: 37 trajectories that reached window_cap at
  L_arch=2047. The territory v2 needs to resolve.

Two complementary feature panels, computed only from persisted records:

1. **Last-N panels** — features over the *last-N tokens regardless of
   where the trajectory stopped*. Window sizes sweep geometrically:
   32 / 64 / 128 / 256 / 512. Asks: at the truncation tail, how do the
   populations look?
2. **Position-window panels** — features over fixed absolute-position
   buckets [0, 64) / [64, 256) / [256, 1024) / [1024, 2048). Captured
   trajectories populate only the buckets their length reaches. Asks:
   is per-step certainty collapse a *depth* phenomenon (universal
   asymptote of self-conditioning) or a *basin* phenomenon (specific
   to commitment to a stable pattern)? And: where do the
   captured-vs-uncaptured distributions converge?

Tabular output groups summary stats (min/p25/median/p75/max) by
terminal_event for each (feature, window) cell, plus a per-trajectory
trace for the window_cap population so depth-collapse shape is visible.

Read-only renderer: no model load, no inference. Tokenizer-free —
decoded `token` text is on each StepRecord.

Run via: uv run python scripts/v2_calibration_probe.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from statistics import mean

from peirce.records import StepRecord
from peirce.runner import default_store_path
from peirce.store import open_store, read_observation


WINDOWS = (32, 64, 128, 256, 512)
# Absolute-position buckets [start, end). Captured trajectories only populate
# buckets their observed_length reaches. Half-open so a trajectory of length 64
# falls into [0, 64) only.
POSITION_WINDOWS: tuple[tuple[int, int], ...] = (
    (0, 64),
    (64, 256),
    (256, 1024),
    (1024, 2048),
)
# (feature_name, accessor, "min" or "max" — direction toward "more in basin")
FEATURES: list[tuple[str, callable, str]] = [
    ("entropy",   lambda s: s.entropy,   "min"),
    ("logit_gap", lambda s: s.logit_gap, "max"),
    ("alt_prob",  lambda s: s.alt_prob,  "min"),
    ("log_prob",  lambda s: s.log_prob,  "max"),
]
MIN_BUCKET_STEPS = 8  # Skip a position-window if a trajectory contributes <N steps.


# Predicate signature that identifies the canonical fp16 selection-bias run.
# Cycle params 32/256, no budget_cap, window_cap=2048.
SELBIAS_PRED_NAMES = {"eos", "basin_capture", "window_cap"}
SELBIAS_BASIN_PARAMS = {"max_period": 32, "cycle_window": 256, "min_repetitions": 4}


def is_selection_bias_obs(predicates_json: str) -> bool:
    preds = json.loads(predicates_json)
    names = {p["name"] for p in preds}
    if names != SELBIAS_PRED_NAMES:
        return False
    for p in preds:
        if p["name"] == "basin_capture":
            if p["params"] != SELBIAS_BASIN_PARAMS:
                return False
    return True


def percentile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return float("nan")
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = q * (len(sorted_vals) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def summarize(vals: list[float]) -> tuple[float, float, float, float, float]:
    s = sorted(vals)
    return (
        s[0],
        percentile(s, 0.25),
        percentile(s, 0.50),
        percentile(s, 0.75),
        s[-1],
    )


def window_features(
    steps: list[StepRecord], window: int
) -> dict[str, dict[str, float]]:
    """Compute mean and min/max-aligned feature values over the last `window` steps."""
    tail = steps[-window:] if len(steps) >= window else steps
    out: dict[str, dict[str, float]] = {}
    for name, accessor, direction in FEATURES:
        vals = [accessor(s) for s in tail]
        out[name] = {
            "mean": mean(vals),
            # "extreme" = the value most consistent with "in-basin":
            # min entropy / alt_prob, max logit_gap / log_prob.
            "extreme": min(vals) if direction == "min" else max(vals),
        }
    return out


def position_window_features(
    steps: list[StepRecord], start: int, end: int
) -> dict[str, dict[str, float]] | None:
    """Compute features over absolute positions [start, end) of `steps`.

    Returns None if the trajectory contributes fewer than MIN_BUCKET_STEPS
    to the bucket — the bucket is then absent from this trajectory's panel.
    """
    if start >= len(steps):
        return None
    slice_ = steps[start:end]
    if len(slice_) < MIN_BUCKET_STEPS:
        return None
    out: dict[str, dict[str, float]] = {}
    for name, accessor, direction in FEATURES:
        vals = [accessor(s) for s in slice_]
        out[name] = {
            "mean": mean(vals),
            "extreme": min(vals) if direction == "min" else max(vals),
        }
    return out


def preview(text: str, width: int = 100) -> str:
    rendered = text.replace("\n", "\\n").replace("\t", "\\t")
    if len(rendered) > width:
        rendered = rendered[: width - 3] + "..."
    return rendered


def main() -> None:
    store_path = default_store_path()
    print(f"Store: {store_path}")
    conn = open_store(store_path)

    # Pull all observations, filter to canonical selection-bias predicate set.
    rows = conn.execute(
        """SELECT observation_id, predicates_json, terminal_event, observed_length
           FROM observations"""
    ).fetchall()
    selbias_oids = [
        (oid, terminal, observed_length)
        for (oid, preds_json, terminal, observed_length) in rows
        if is_selection_bias_obs(preds_json)
    ]
    print(f"Selection-bias observations: {len(selbias_oids)}")
    by_terminal: dict[str, int] = defaultdict(int)
    for _, t, _ in selbias_oids:
        by_terminal[t] += 1
    print(f"By terminal: {dict(by_terminal)}\n")

    # Compute per-trajectory feature panels.
    # panels[oid] = {(window, feature, "mean"|"extreme"): float}
    # pos_panels[oid] = {(start, end): {feature: {"mean": v, "extreme": v}}}
    panels: dict[str, dict[tuple[int, str, str], float]] = {}
    pos_panels: dict[str, dict[tuple[int, int], dict[str, dict[str, float]]]] = {}
    terminals: dict[str, str] = {}
    lengths: dict[str, int] = {}
    tail_texts: dict[str, str] = {}

    for oid, terminal, observed_length in selbias_oids:
        obs = read_observation(conn, oid)
        # Read the FULL trajectory (now extended to L_arch by full_depth_extension),
        # not the truncated obs.steps view. This lets us inspect what the v1 cycle-
        # captured trajectories *did* past their truncation point — which is what
        # the depth-collapse hypothesis turns on. The original observed_length is
        # kept around as `lengths[oid]` for the per-trajectory display.
        steps = obs.trajectory.steps
        if len(steps) < 2:
            continue
        terminals[oid] = terminal
        lengths[oid] = obs.observed_length
        # Last 64 tokens of the *full* trajectory — for cycle-captured ones this
        # is now the post-capture tail at L_arch, not the at-capture truncation.
        tail_texts[oid] = "".join(s.token for s in steps[-64:])
        cells: dict[tuple[int, str, str], float] = {}
        for w in WINDOWS:
            feats = window_features(steps, w)
            for fname in feats:
                cells[(w, fname, "mean")] = feats[fname]["mean"]
                cells[(w, fname, "extreme")] = feats[fname]["extreme"]
        panels[oid] = cells
        pos_buckets: dict[tuple[int, int], dict[str, dict[str, float]]] = {}
        for start, end in POSITION_WINDOWS:
            feats = position_window_features(steps, start, end)
            if feats is not None:
                pos_buckets[(start, end)] = feats
        pos_panels[oid] = pos_buckets

    # Group oids by terminal event.
    by_term: dict[str, list[str]] = defaultdict(list)
    for oid, term in terminals.items():
        by_term[term].append(oid)

    # Aggregate summary tables: for each (feature, agg, window), print
    # min / p25 / median / p75 / max for each terminal-event population.
    print("=" * 120)
    print("Population summary stats: last-N feature distributions")
    print("=" * 120)
    print()
    header = f"{'feature':<10} {'agg':<7} {'window':>6} {'pop':<15} {'n':>4}  "
    header += f"{'min':>8} {'p25':>8} {'p50':>8} {'p75':>8} {'max':>8}"

    for fname, _, _ in FEATURES:
        for agg in ("mean", "extreme"):
            print(header)
            print("-" * len(header))
            for w in WINDOWS:
                for term, oids in sorted(by_term.items()):
                    vals = [panels[oid][(w, fname, agg)] for oid in oids if oid in panels]
                    if not vals:
                        continue
                    mn, p25, p50, p75, mx = summarize(vals)
                    print(
                        f"{fname:<10} {agg:<7} {w:>6} {term:<15} {len(vals):>4}  "
                        f"{mn:>8.3f} {p25:>8.3f} {p50:>8.3f} {p75:>8.3f} {mx:>8.3f}"
                    )
                print()
            print()

    # Position-window summaries: features by absolute-position bucket, grouped
    # by terminal_event. A trajectory contributes to a bucket only if its
    # observed_length covers at least MIN_BUCKET_STEPS of the bucket.
    print("=" * 120)
    print("Position-window summary stats: features by absolute-position bucket")
    print(f"(buckets: {[f'[{s},{e})' for s, e in POSITION_WINDOWS]}; min "
          f"{MIN_BUCKET_STEPS} steps required)")
    print("=" * 120)
    print()
    pheader = (
        f"{'feature':<10} {'agg':<7} {'bucket':>13} {'pop':<15} {'n':>4}  "
        f"{'min':>8} {'p25':>8} {'p50':>8} {'p75':>8} {'max':>8}"
    )
    for fname, _, _ in FEATURES:
        for agg in ("mean", "extreme"):
            print(pheader)
            print("-" * len(pheader))
            for start, end in POSITION_WINDOWS:
                bucket_label = f"[{start},{end})"
                for term, oids in sorted(by_term.items()):
                    vals = [
                        pos_panels[oid][(start, end)][fname][agg]
                        for oid in oids
                        if oid in pos_panels and (start, end) in pos_panels[oid]
                    ]
                    if not vals:
                        continue
                    mn, p25, p50, p75, mx = summarize(vals)
                    print(
                        f"{fname:<10} {agg:<7} {bucket_label:>13} {term:<15} "
                        f"{len(vals):>4}  "
                        f"{mn:>8.3f} {p25:>8.3f} {p50:>8.3f} {p75:>8.3f} {mx:>8.3f}"
                    )
                print()
            print()

    # Entropy-onset analysis: per-trajectory position at which entropy first
    # drops below threshold for `ONSET_SMOOTHING` consecutive steps. Asks a
    # cleaner version of the depth-collapse question: at what depth does each
    # trajectory cross the deterministic floor, and is the distribution the
    # same across terminal-event populations?
    onset_thresh = 0.1
    onset_smoothing = 8
    print("=" * 120)
    print(
        f"Entropy-onset distribution: first position with {onset_smoothing} "
        f"consecutive steps below {onset_thresh}"
    )
    print("=" * 120)
    print()

    onset_by_term: dict[str, list[int]] = defaultdict(list)
    onset_never: dict[str, list[str]] = defaultdict(list)
    for oid in panels:  # only the trajectories the probe could panel
        steps = read_observation(conn, oid).trajectory.steps
        consecutive = 0
        onset = None
        for i, s in enumerate(steps):
            if s.entropy < onset_thresh:
                consecutive += 1
                if consecutive >= onset_smoothing:
                    onset = i - onset_smoothing + 1
                    break
            else:
                consecutive = 0
        if onset is None:
            onset_never[terminals[oid]].append(oid)
        else:
            onset_by_term[terminals[oid]].append(onset)

    print(
        f"{'pop':<18} {'n':>4} {'min':>5} {'p25':>5} {'p50':>5} {'p75':>5} {'max':>5}"
        f"  never_below"
    )
    for term in sorted(onset_by_term):
        s = sorted(onset_by_term[term])
        mn, p25, p50, p75, mx = summarize(s)
        nb = len(onset_never.get(term, []))
        print(
            f"{term:<18} {len(s):>4} {int(mn):>5} {int(p25):>5} {int(p50):>5} "
            f"{int(p75):>5} {int(mx):>5}  {nb}"
        )
    print()

    print("Distribution by depth bucket:")
    buckets = [(0, 64), (64, 256), (256, 512), (512, 1024), (1024, 2048)]
    print(
        f"{'pop':<18} "
        + " ".join(f"[{a},{b})".rjust(11) for a, b in buckets)
        + "  never"
    )
    for term in sorted(onset_by_term):
        counts = [sum(1 for v in onset_by_term[term] if a <= v < b) for a, b in buckets]
        nb = len(onset_never.get(term, []))
        print(
            f"{term:<18} "
            + " ".join(str(c).rjust(11) for c in counts)
            + f"  {nb}"
        )
    print()

    if onset_never:
        print(
            "Never-below trajectories (entropy stays above threshold throughout) — "
            "these are the loose-asymptote captures (prose-cycle basins where late-"
            "window entropy stays elevated):"
        )
        for term, oids in onset_never.items():
            for oid in oids:
                print(f"  [{term}] {oid[:8]}  tail: {preview(tail_texts[oid], 80)}")
        print()

    # Per-trajectory entropy trace across position-windows for the window_cap
    # population. Visualizes the depth-collapse shape per trajectory: is
    # entropy already low at [0, 64), or does it transition somewhere?
    print("=" * 120)
    print("Per-trajectory entropy trace across position-windows: window_cap population")
    print("(entropy mean per bucket, sorted by [0,64) entropy mean)")
    print("=" * 120)
    bucket_labels = [f"[{s},{e})" for s, e in POSITION_WINDOWS]
    header_cells = "  ".join(f"{b:>13}" for b in bucket_labels)
    print(f"{'oid':<10} {'len':>5}  {header_cells}  tail_preview")
    print("-" * 120)
    wc_oids_pos = sorted(
        [oid for oid in by_term.get("window_cap", []) if oid in pos_panels],
        key=lambda oid: pos_panels[oid].get(
            (0, 64), {}
        ).get("entropy", {}).get("mean", float("inf")),
    )
    for oid in wc_oids_pos:
        cells_str_parts = []
        for start, end in POSITION_WINDOWS:
            bucket = pos_panels[oid].get((start, end))
            if bucket is None:
                cells_str_parts.append(f"{'-':>13}")
            else:
                cells_str_parts.append(f"{bucket['entropy']['mean']:>13.3f}")
        print(
            f"{oid[:8]:<10} {lengths[oid]:>5}  "
            f"{'  '.join(cells_str_parts)}  {preview(tail_texts[oid], 60)}"
        )
    print()

    # Same trace for candidate-basin trajectories that reached the deeper
    # buckets. Adjudicates whether these "long" cycle-captures look like
    # window_cap trajectories at the same depth.
    print("=" * 120)
    print("Per-trajectory entropy trace: candidate-basin reaching [256,1024) bucket")
    print("(only captures of length >= 256+8; sorted by [0,64) entropy mean)")
    print("=" * 120)
    print(f"{'oid':<10} {'len':>5}  {header_cells}  tail_preview")
    print("-" * 120)
    cb_long = [
        oid for oid in by_term.get("candidate-basin", [])
        if oid in pos_panels and (256, 1024) in pos_panels[oid]
    ]
    cb_long.sort(
        key=lambda oid: pos_panels[oid].get(
            (0, 64), {}
        ).get("entropy", {}).get("mean", float("inf")),
    )
    for oid in cb_long:
        cells_str_parts = []
        for start, end in POSITION_WINDOWS:
            bucket = pos_panels[oid].get((start, end))
            if bucket is None:
                cells_str_parts.append(f"{'-':>13}")
            else:
                cells_str_parts.append(f"{bucket['entropy']['mean']:>13.3f}")
        print(
            f"{oid[:8]:<10} {lengths[oid]:>5}  "
            f"{'  '.join(cells_str_parts)}  {preview(tail_texts[oid], 60)}"
        )
    print()

    # Per-trajectory rows for the window_cap (candidate-positive) population.
    # Show the most informative slices: window=256 mean + extreme, for entropy
    # and logit_gap. Plus the last-64-token text preview to eyeball shape.
    print("=" * 120)
    print("Per-trajectory feature snapshot: window_cap (candidate-positive) population")
    print("(window=256; mean/extreme for entropy and logit_gap)")
    print("=" * 120)
    wc_oids = sorted(
        by_term.get("window_cap", []),
        key=lambda oid: panels[oid][(256, "entropy", "mean")],
    )
    print(
        f"{'oid':<10} {'len':>5}  "
        f"{'H_mean':>7} {'H_min':>7}  {'gap_mean':>8} {'gap_max':>7}  tail_preview"
    )
    print("-" * 120)
    for oid in wc_oids:
        cells = panels[oid]
        print(
            f"{oid[:8]:<10} {lengths[oid]:>5}  "
            f"{cells[(256,'entropy','mean')]:>7.3f} "
            f"{cells[(256,'entropy','extreme')]:>7.3f}  "
            f"{cells[(256,'logit_gap','mean')]:>8.3f} "
            f"{cells[(256,'logit_gap','extreme')]:>7.3f}  "
            f"{preview(tail_texts[oid], 80)}"
        )
    print()

    # Compare against captured (confirmed-positive) population in same slice.
    print("=" * 120)
    print("Per-trajectory feature snapshot: candidate-basin (confirmed-positive) population")
    print("(window=256; mean/extreme for entropy and logit_gap; sorted by H_mean)")
    print("=" * 120)
    cb_oids = sorted(
        by_term.get("candidate-basin", []),
        key=lambda oid: panels[oid][(256, "entropy", "mean")],
    )
    print(
        f"{'oid':<10} {'len':>5}  "
        f"{'H_mean':>7} {'H_min':>7}  {'gap_mean':>8} {'gap_max':>7}  tail_preview"
    )
    print("-" * 120)
    for oid in cb_oids:
        cells = panels[oid]
        print(
            f"{oid[:8]:<10} {lengths[oid]:>5}  "
            f"{cells[(256,'entropy','mean')]:>7.3f} "
            f"{cells[(256,'entropy','extreme')]:>7.3f}  "
            f"{cells[(256,'logit_gap','mean')]:>8.3f} "
            f"{cells[(256,'logit_gap','extreme')]:>7.3f}  "
            f"{preview(tail_texts[oid], 80)}"
        )

    conn.close()


if __name__ == "__main__":
    main()
