"""NOPERIOD specimen audit — read-only diagnostic on the 8 trajectories
the N1.5 catalog tags as NOPERIOD under current convention.

Question. The N1.5 catalog count is SLOTTED 26 / SCAFFOLD 66 / NOPERIOD 8;
N1 first-light under the prior first-peak-above-threshold convention had
NOPERIOD 3. The 5 new NOPERIOD additions came from the strict-local-max
rule replacing first-peak — a rule that returns `[]` when the
autocorrelation rises monotonically through the search window or when a
candidate's neighbours bracket it without strict inequality. This audit
checks whether the additions are honest no-period, just-below-threshold,
or out-of-window.

Per NOPERIOD specimen, reports:

  - peaks under current convention (default reference: PEAK_MIN=0.3,
    lag ∈ [LAG_MIN, LAG_MAX])
  - peaks at relaxed PEAK_MIN (0.20, 0.10) — surfaces specimens whose
    autocorrelation has structured peaks just below the default threshold
  - peaks at widened LAG_MAX (256) under the default and relaxed
    thresholds — surfaces specimens with true period above the default
    LAG_MAX
  - top-K normalized-acf values across the wide lag window with no
    strict-local-max filter — surfaces where signal sits if any, even
    when the strict-local-max test rejects every candidate

Plus deep-window H, gap, gap_over_H quartile summaries for orientation.

Read-only over `data/peirce.db`. Same selection-bias filter as
`shape_catalog.py`. No model load, no inference.

Run via: uv run python scripts/noperiod_audit.py
"""
from __future__ import annotations

import json

import numpy as np

from peirce.runner import default_store_path
from peirce.shape import DEEP_START, LAG_MAX, LAG_MIN, PEAK_MIN, acf_peaks, dominant_period
from peirce.store import open_store, read_observation


SELBIAS_PRED_NAMES = {"eos", "basin_capture", "window_cap"}
SELBIAS_BASIN_PARAMS = {"max_period": 32, "cycle_window": 256, "min_repetitions": 4}

GAP_OVER_H_EPS = 1e-4
WIDE_LAG_MAX = 256
RELAXED_PEAK_MINS = (0.20, 0.10)
TOP_K_RAW_ACF = 5
NOISE_FLOOR_STD = 1e-4   # mirrors peirce.shape's private constant


def is_selection_bias_obs(predicates_json: str) -> bool:
    preds = json.loads(predicates_json)
    names = {p["name"] for p in preds}
    if names != SELBIAS_PRED_NAMES:
        return False
    for p in preds:
        if p["name"] == "basin_capture" and p["params"] != SELBIAS_BASIN_PARAMS:
            return False
    return True


def normalized_acf(x: np.ndarray, max_lag: int) -> np.ndarray | None:
    """Normalized autocorrelation up to `max_lag`. Returns the full array
    `ac[0..max_lag]` (so `ac[lag]` is the normalized acf at that lag).
    None if the signal is too short or zero-variance — same preconditions
    as `peirce.shape.acf_peaks`."""
    if x.size < max_lag * 2:
        return None
    x = x - x.mean()
    if x.std() < NOISE_FLOOR_STD:
        return None
    n = x.size
    ac = np.correlate(x, x, mode="full")[n - 1:]
    if ac[0] <= 0:
        return None
    return ac / ac[0]


def quartile_summary(arr: np.ndarray) -> dict:
    if arr.size == 0:
        return {"median": float("nan"), "q1": float("nan"), "q3": float("nan"),
                "min": float("nan"), "max": float("nan")}
    return {
        "median": float(np.median(arr)),
        "q1": float(np.percentile(arr, 25)),
        "q3": float(np.percentile(arr, 75)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def format_quartile(q: dict, fmt: str = ".4f") -> str:
    return (f"median={q['median']:{fmt}} IQR=[{q['q1']:{fmt}}, {q['q3']:{fmt}}] "
            f"min={q['min']:{fmt}} max={q['max']:{fmt}}")


def format_peaks(peaks: list[tuple[int, float]]) -> str:
    if not peaks:
        return "[]"
    return "[" + ", ".join(f"({lag},{val:.2f})" for lag, val in peaks) + "]"


def main() -> None:
    conn = open_store(default_store_path())
    rows = conn.execute(
        "SELECT observation_id, predicates_json FROM observations"
    ).fetchall()

    noperiod_oids: list[str] = []
    h_traces: dict[str, np.ndarray] = {}
    gap_traces: dict[str, np.ndarray] = {}

    for oid, preds_json in rows:
        if not is_selection_bias_obs(preds_json):
            continue
        obs = read_observation(conn, oid)
        steps = obs.trajectory.steps
        if len(steps) < DEEP_START + 256:
            continue
        deep = steps[DEEP_START:]
        H = np.fromiter((s.entropy for s in deep), dtype=np.float32)
        gap = np.fromiter((s.logit_gap for s in deep), dtype=np.float32)
        if dominant_period(H) is None:
            noperiod_oids.append(oid)
            h_traces[oid] = H
            gap_traces[oid] = gap

    conn.close()

    print(f"NOPERIOD specimen audit — {len(noperiod_oids)} trajectories under default convention")
    print(f"defaults:    PEAK_MIN={PEAK_MIN}, lag ∈ [{LAG_MIN}, {LAG_MAX}], deep window [{DEEP_START}, end)")
    print(f"audit knobs: relaxed PEAK_MIN ∈ {RELAXED_PEAK_MINS}, wide LAG_MAX={WIDE_LAG_MAX}")
    print()

    for oid in noperiod_oids:
        H = h_traces[oid]
        gap = gap_traces[oid]
        gap_over_H_step = gap / np.maximum(H, GAP_OVER_H_EPS)

        print(f"--- {oid[:8]} ({oid}) ---")
        print(f"   deep H:          {format_quartile(quartile_summary(H))}")
        print(f"   deep gap:        {format_quartile(quartile_summary(gap), '.3f')}")
        print(f"   deep gap_over_H: {format_quartile(quartile_summary(gap_over_H_step), '.1f')}")

        peaks_default = acf_peaks(H)
        print(f"   peaks (PEAK_MIN={PEAK_MIN}, lag≤{LAG_MAX}):  {format_peaks(peaks_default)}")
        for pm in RELAXED_PEAK_MINS:
            relaxed = acf_peaks(H, peak_min=pm)
            print(f"   peaks (PEAK_MIN={pm}, lag≤{LAG_MAX}): {format_peaks(relaxed)}")
        wide = acf_peaks(H, lag_max=WIDE_LAG_MAX)
        print(f"   peaks (PEAK_MIN={PEAK_MIN}, lag≤{WIDE_LAG_MAX}): {format_peaks(wide)}")
        wide_relaxed = acf_peaks(H, lag_max=WIDE_LAG_MAX, peak_min=0.10)
        print(f"   peaks (PEAK_MIN=0.10, lag≤{WIDE_LAG_MAX}):{format_peaks(wide_relaxed)}")

        ac = normalized_acf(H, max_lag=WIDE_LAG_MAX)
        if ac is None:
            print(f"   normalized acf: signal too short or zero-variance")
        else:
            ac_window = ac[LAG_MIN : WIDE_LAG_MAX + 1]
            argsorted = np.argsort(-ac_window)
            print(f"   top-{TOP_K_RAW_ACF} acf values in lag ∈ [{LAG_MIN}, {WIDE_LAG_MAX}] (no peak filter):")
            for k in argsorted[:TOP_K_RAW_ACF]:
                lag = int(k) + LAG_MIN
                print(f"      lag={lag:4d}  acf={float(ac_window[k]):.3f}")
        print()


if __name__ == "__main__":
    main()
