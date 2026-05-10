"""Shape primitives over per-step record arrays.

Pure functions over numpy arrays of per-step quantities — no engine, no
store, no model. The deep window convention `DEEP_START = 1024` is exported
from here for consumers that compute metrics over the canonical window.

Project-level shape primitives live here (where multiple consumers warrant
sharing); per-script aggregations of these primitives (median, std, ratio)
remain inline in the consumer.

Functions:

  - `entropy_onset(entropy)` — first position holding entropy below
    `ONSET_THRESHOLD` for `ONSET_SMOOTHING` consecutive steps. Collapse-
    speed scalar.
  - `acf_peaks(x)` — local maxima of the normalized autocorrelation of the
    mean-subtracted signal in `[LAG_MIN, LAG_MAX]`, filtered above
    `PEAK_MIN`, ordered by lag. The underlying period measurement; clean
    periodic signals show a harmonic ladder, multi-period structure shows
    multiple non-multiple lags, NOPERIOD signals return the empty list.
  - `dominant_period(x)` — first peak (lowest lag) from `acf_peaks` as a
    single-int convention. Fundamental period under the convention; `None`
    when no peaks.

Convention change vs the prior `argmax`-in-window implementation: an
autocorrelation that rises monotonically through the search window (true
period above `LAG_MAX`) now returns `[]` / `None`, where the prior version
returned `lag_max`. This is a contract-level change at the boundary; for
specimens with true period within the window the new function returns the
fundamental rather than a harmonic.
"""
from __future__ import annotations

import numpy as np


DEEP_START: int = 1024
"""Left edge of the canonical deep window `[DEEP_START, end)`."""

ONSET_THRESHOLD: float = 0.1
ONSET_SMOOTHING: int = 8

LAG_MIN: int = 2
LAG_MAX: int = 128
PEAK_MIN: float = 0.3

_NOISE_FLOOR_STD: float = 1e-4


def entropy_onset(
    entropy: np.ndarray,
    threshold: float = ONSET_THRESHOLD,
    smoothing: int = ONSET_SMOOTHING,
) -> int | None:
    """First position where `smoothing` consecutive steps stay below `threshold`."""
    consecutive = 0
    for i, e in enumerate(entropy):
        if e < threshold:
            consecutive += 1
            if consecutive >= smoothing:
                return i - smoothing + 1
        else:
            consecutive = 0
    return None


def acf_peaks(
    x: np.ndarray,
    lag_min: int = LAG_MIN,
    lag_max: int = LAG_MAX,
    peak_min: float = PEAK_MIN,
) -> list[tuple[int, float]]:
    """Local maxima of the normalized autocorrelation in `[lag_min, lag_max]`
    above `peak_min`, ordered by lag.

    A *peak* is a strict local maximum: `ac[lag] > ac[lag-1]` and
    `ac[lag] > ac[lag+1]`. Both neighbours are always defined under the
    `x.size >= 2 * lag_max` precondition (which the function enforces by
    returning `[]` for shorter signals).

    Each entry is `(lag, normalized_acf_value)`. The list is the underlying
    period measurement — harmonic ladders show as multiple entries at
    integer multiples of the fundamental, multi-period structure shows as
    non-multiple lags, NOPERIOD signals return `[]`.
    """
    if x.size < lag_max * 2:
        return []
    x = x - x.mean()
    if x.std() < _NOISE_FLOOR_STD:
        return []
    n = x.size
    ac = np.correlate(x, x, mode="full")[n - 1:]
    if ac[0] <= 0:
        return []
    ac = ac / ac[0]
    peaks: list[tuple[int, float]] = []
    for lag in range(lag_min, lag_max + 1):
        v = float(ac[lag])
        if v < peak_min:
            continue
        if ac[lag] > ac[lag - 1] and ac[lag] > ac[lag + 1]:
            peaks.append((lag, v))
    return peaks


def dominant_period(
    x: np.ndarray,
    lag_min: int = LAG_MIN,
    lag_max: int = LAG_MAX,
    peak_min: float = PEAK_MIN,
) -> int | None:
    """First peak (lowest lag) from `acf_peaks` — fundamental period under the convention.

    `None` when `acf_peaks` returns the empty list (signal variance below
    noise, or no local maximum in window crosses `peak_min`).
    """
    peaks = acf_peaks(x, lag_min=lag_min, lag_max=lag_max, peak_min=peak_min)
    return peaks[0][0] if peaks else None
