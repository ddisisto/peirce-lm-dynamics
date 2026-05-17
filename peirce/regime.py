"""Regime-tag resolver — structured tag derivation from substrate primitives.

Pure functions over `StepRecord` sequences. Sibling to `peirce/shape.py`,
depends on its primitives (`acf_peaks`, `dominant_period`, `DEEP_START`).

The taxonomy carries three orthogonal axes, surfaced by the audit pass that
preceded this module (`scripts/regime_tag_audit.py`, findings in
`notes/regime-tag-consolidation.md`):

  - **umbrella** — `SLOTTED` / `SCAFFOLD` / `NOPERIOD`. The coarsest
    partition; derived from period detection + presence of non-degenerate
    chosen-token distributions at phase positions. `SLOTTED` and `SCAFFOLD`
    both require a detectable period; the split is on whether any phase
    position is a *slot* (chosen-token entropy across recurrences above
    `SLOT_H_EPS`).
  - **slot_character** — for `SLOTTED` umbrella only: `CLASS` /
    `COUNTER-INT` / `COUNTER-LETTER` / `MIXED`. Names the structure of the
    slot's chosen-token sequence in recurrence order. The COUNTER tags are
    a heuristic over int / single-letter successive-delta evidence; `MIXED`
    fires when distinct slot tags coexist across phase positions in the
    same trajectory.
  - **peak_structure** — `HARMONIC` or `None`. Strict harmonic-ladder
    predicate over `acf_peaks`: requires at least `HARMONIC_MIN_PEAKS`
    peaks, with peaks[1..k-1] at integer multiples of peaks[0] within
    `HARMONIC_LAG_TOLERANCE`. The strict definition was chosen against the
    looser N1 annotator reading per audit finding 2 — the strict bucket
    represents the clean integer-multiple-ladder population specifically.
    Orthogonal to slot/scaffold; fires across both umbrellas.

The `NOPERIOD` umbrella has its own sub-axis (`noperiod_cluster`: `A` or
`B`). `A` is honest no-period (no peaks even at relaxed PEAK_MIN);
`B` is weak-sub-threshold-structure (peaks exist at relaxed but not
default PEAK_MIN). The "bimodal H" half of the B definition from
`notes/regime-tag-consolidation.md` is not yet operationalised — the
relaxed-peak axis alone agreed with the manifest at n=8 in the audit
(5/5 A and 3/3 B), so the split lands without the H-mode check for now.
H is reported alongside on the tag for downstream qualitative use.

The module is foundation-stable in the sense `design-reqs.md` requires:
the tag is a pure function of per-step records via `shape.py` primitives,
so cycle-3 inheritance is via the substrate, not the cycle-2 taxonomy.
Predicates are revisable; the *function-from-substrate* commitment is not.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Literal

import numpy as np

from peirce.records import StepRecord
from peirce.shape import DEEP_START, acf_peaks, dominant_period


SLOT_H_EPS: float = 1e-3
"""Chosen-token Shannon entropy threshold (nats) above which a phase
position is a slot. Matches `shape_catalog.py`'s inline rule."""

COUNTER_MATCH_THRESHOLD: float = 0.75
"""Successive-delta match fraction above which a slot's chosen sequence
tags as a COUNTER (consecutive ints or letters)."""

HARMONIC_MIN_PEAKS: int = 3
"""Minimum peak count for the strict HARMONIC ladder predicate."""

HARMONIC_LAG_TOLERANCE: int = 1
"""Absolute lag tolerance (steps) around each predicted integer multiple
of peaks[0] in the HARMONIC ladder check."""

NOPERIOD_B_RELAXED_PEAK_MIN: float = 0.10
"""Relaxed peak threshold used to split NOPERIOD into A (no peaks even
here) and B (peaks here, but not at default PEAK_MIN)."""


Umbrella = Literal["SLOTTED", "SCAFFOLD", "NOPERIOD"]
SlotCharacter = Literal["CLASS", "COUNTER-INT", "COUNTER-LETTER", "MIXED"]
PeakStructure = Literal["HARMONIC"]
NoperiodCluster = Literal["A", "B"]


@dataclass(frozen=True)
class RegimeTag:
    """Structured regime tag.

    Axes are orthogonal: `peak_structure` can be set on either SLOTTED or
    SCAFFOLD; `slot_character` is set only on SLOTTED; `noperiod_cluster`
    is set only on NOPERIOD. The `flat` property emits a flat string for
    consumers that want one (loses no information unless multiple axes
    are set, in which case it carries the SLOTTED-character form and
    drops peak_structure — the flat form is for display, not comparison)."""

    umbrella: Umbrella
    slot_character: SlotCharacter | None = None
    peak_structure: PeakStructure | None = None
    noperiod_cluster: NoperiodCluster | None = None

    @property
    def flat(self) -> str:
        if self.umbrella == "NOPERIOD":
            return f"NOPERIOD-{self.noperiod_cluster}" if self.noperiod_cluster else "NOPERIOD"
        if self.umbrella == "SCAFFOLD":
            return "SCAFFOLD+HARMONIC" if self.peak_structure == "HARMONIC" else "SCAFFOLD"
        # SLOTTED
        base = f"SLOTTED-{self.slot_character}" if self.slot_character else "SLOTTED"
        return f"{base}+HARMONIC" if self.peak_structure == "HARMONIC" else base


def _shannon_H_nats(counter: Counter) -> float:
    total = sum(counter.values())
    if total <= 1:
        return 0.0
    H = 0.0
    for c in counter.values():
        if c == 0:
            continue
        p = c / total
        H -= p * np.log(p)
    return float(H)


def _slot_character(chosen_seq: list[str]) -> SlotCharacter:
    """Tag a slot's chosen-token sequence as CLASS or one of the COUNTER
    variants. Mirrors `shape_catalog.py`'s slot_chosen_evidence rule."""
    stripped = [t.strip() for t in chosen_seq]
    n_pairs = max(0, len(stripped) - 1)
    if n_pairs == 0:
        return "CLASS"
    try:
        ints = [int(t) for t in stripped]
        deltas = np.diff(np.asarray(ints))
        med = int(np.median(deltas))
        frac = float(np.mean(deltas == med))
        if med in (1, -1) and frac >= COUNTER_MATCH_THRESHOLD:
            return "COUNTER-INT"
    except (ValueError, TypeError):
        pass
    if all(len(t) == 1 and t.isascii() and t.isalpha() for t in stripped):
        ords = np.asarray([ord(t) for t in stripped])
        deltas = np.diff(ords)
        med = int(np.median(deltas))
        frac = float(np.mean(deltas == med))
        if med in (1, -1) and frac >= COUNTER_MATCH_THRESHOLD:
            return "COUNTER-LETTER"
    return "CLASS"


def _harmonic_ladder(peaks: list[tuple[int, float]]) -> bool:
    """Strict HARMONIC predicate: at least HARMONIC_MIN_PEAKS peaks, with
    peaks[1..k-1] at integer multiples of peaks[0] within
    HARMONIC_LAG_TOLERANCE. The first peak is taken as the fundamental."""
    if len(peaks) < HARMONIC_MIN_PEAKS:
        return False
    lag0 = peaks[0][0]
    if lag0 <= 0:
        return False
    for lag, _val in peaks[1:HARMONIC_MIN_PEAKS]:
        ratio = round(lag / lag0)
        if ratio < 2:
            return False
        if abs(lag - ratio * lag0) > HARMONIC_LAG_TOLERANCE:
            return False
    return True


def _noperiod_cluster(H: np.ndarray) -> NoperiodCluster:
    """A when no peaks even at relaxed PEAK_MIN; B otherwise (weak
    quasi-periodic peaks below the default threshold)."""
    relaxed = acf_peaks(H, peak_min=NOPERIOD_B_RELAXED_PEAK_MIN)
    return "A" if not relaxed else "B"


def regime_tag(steps: list[StepRecord], deep_start: int = DEEP_START) -> RegimeTag:
    """Structured regime tag derived from substrate primitives.

    Requires `len(steps) > deep_start` (raises `ValueError` otherwise). The
    deep window `[deep_start, end)` is the surface over which all axes
    derive — period detection, slot identification, slot-character
    tagging, harmonic-ladder check, NOPERIOD-cluster split.

    The tag is a pure function of `steps` (modulo `shape.py` constants);
    no model, no store, no I/O.
    """
    if len(steps) <= deep_start:
        raise ValueError(
            f"trajectory has {len(steps)} steps; need > {deep_start} for the deep window"
        )

    deep = steps[deep_start:]
    H = np.fromiter((s.entropy for s in deep), dtype=np.float32)
    peaks = acf_peaks(H)
    period = dominant_period(H)
    harmonic = "HARMONIC" if _harmonic_ladder(peaks) else None

    if period is None:
        return RegimeTag(
            umbrella="NOPERIOD",
            noperiod_cluster=_noperiod_cluster(H),
        )

    slot_chars: set[SlotCharacter] = set()
    for phase in range(period):
        idxs = np.arange(phase, len(deep), period)
        if idxs.size == 0:
            continue
        chosen_counter: Counter = Counter()
        chosen_seq: list[str] = []
        for i in idxs:
            step = deep[int(i)]
            chosen_counter[step.token] += 1
            chosen_seq.append(step.token)
        if _shannon_H_nats(chosen_counter) > SLOT_H_EPS:
            slot_chars.add(_slot_character(chosen_seq))

    if not slot_chars:
        return RegimeTag(umbrella="SCAFFOLD", peak_structure=harmonic)

    if len(slot_chars) == 1:
        (only,) = slot_chars
        slot_character: SlotCharacter = only
    else:
        slot_character = "MIXED"

    return RegimeTag(
        umbrella="SLOTTED",
        slot_character=slot_character,
        peak_structure=harmonic,
    )
