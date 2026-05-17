"""Regime-tag audit — surface what the substrate's shape primitives say about
regime tags vs what the manifest in `first_batch_branches.BATCH` carries.

Transitional script. Output informs the design of `peirce/regime.py` (the
resolver module that will lift regime-tag derivation out of `shape_catalog.py`'s
inline logic and `noperiod_audit.py`'s script-local A/B split, and pin
`SLOTTED-HARMONIC` as a real predicate rather than an observational shorthand).
Lifecycle pinned in `notes/regime-tag-consolidation.md`.

For every trajectory in the store with `len(steps) >= DEEP_START + 256`,
reports:

  - catalog-emitted regime tag (`SLOTTED-CLASS` / -COUNTER-INT / -COUNTER-LETTER
    / -MIXED / SCAFFOLD / NOPERIOD), derived inline using the same period +
    slot-evidence rules as `shape_catalog.py`
  - SLOTTED-HARMONIC candidate flag — first-cut predicate over `peaks`:
    len >= HARMONIC_MIN_PEAKS, and `peaks[1].lag` and `peaks[2].lag` are
    integer multiples of `peaks[0].lag` within `HARMONIC_LAG_TOLERANCE`
  - NOPERIOD A/B candidate — A when no peaks even at relaxed PEAK_MIN=0.10,
    B when at least one peak at relaxed-0.10 (weak quasi-periodic structure
    below the catalog's default threshold). The "bimodal H" half of the
    B definition from `notes/regime-tag-consolidation.md` is deferred to a
    later operational pass; reported as `B?` here for now and the H mode
    check is shown qualitatively via the H IQR
  - manifest tag from `first_batch_branches.BATCH` if present (else "—")
  - raw shape primitives: `peaks`, `floor_H`, `osc_amp`

Then a summary section with:

  - counts by derived umbrella tag
  - manifest-vs-derived agreement matrix (only over the 25 BATCH entries)
  - cross-tag overlaps (e.g. specimens that are both SLOTTED-CLASS and
    SLOTTED-HARMONIC, since slot-character and peak-structure axes may be
    orthogonal — the audit settles whether they are)

Read-only over `data/peirce.db`. No model load, no inference.

Run via: uv run python scripts/regime_tag_audit.py
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from first_batch_branches import BATCH  # noqa: E402

from peirce.runner import default_store_path
from peirce.shape import DEEP_START, acf_peaks, dominant_period
from peirce.store import open_store, read_trajectory


SLOT_H_EPS = 1e-3
COUNTER_MATCH_THRESHOLD = 0.75
GAP_OVER_H_EPS = 1e-4

HARMONIC_MIN_PEAKS = 3
HARMONIC_LAG_TOLERANCE = 1  # absolute steps either side of the predicted multiple
NOPERIOD_B_RELAXED_PEAK_MIN = 0.10


def shannon_H_nats(counter: Counter) -> float:
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


def slot_chosen_tag(chosen_seq: list[str]) -> str:
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


def catalog_regime_tag(steps) -> tuple[str, list[tuple[int, float]], int | None]:
    """Returns (tag, peaks, period). Mirrors shape_catalog's inline rules."""
    deep = steps[DEEP_START:]
    H = np.fromiter((s.entropy for s in deep), dtype=np.float32)
    peaks = acf_peaks(H)
    period = dominant_period(H)
    if period is None:
        return "NOPERIOD", peaks, None

    slot_tags: set[str] = set()
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
        if shannon_H_nats(chosen_counter) > SLOT_H_EPS:
            slot_tags.add(slot_chosen_tag(chosen_seq))

    if not slot_tags:
        return "SCAFFOLD", peaks, period
    if slot_tags == {"COUNTER-INT"}:
        return "SLOTTED-COUNTER-INT", peaks, period
    if slot_tags == {"COUNTER-LETTER"}:
        return "SLOTTED-COUNTER-LETTER", peaks, period
    if slot_tags == {"CLASS"}:
        return "SLOTTED-CLASS", peaks, period
    return "SLOTTED-MIXED", peaks, period


def harmonic_candidate(peaks: list[tuple[int, float]]) -> bool:
    """First-cut SLOTTED-HARMONIC predicate. True when the autocorrelation
    shows a clean harmonic ladder rooted at peaks[0]: the next two peaks fall
    at integer multiples of the fundamental within HARMONIC_LAG_TOLERANCE."""
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


def noperiod_cluster(steps) -> str:
    """A: no peaks even at relaxed PEAK_MIN=0.10. B?: at least one peak at
    relaxed PEAK_MIN=0.10 but not at default — weak quasi-periodic structure.
    `?` marks the bimodal-H half of the B definition as not yet operationalised
    in this audit; see notes/regime-tag-consolidation.md."""
    deep = steps[DEEP_START:]
    H = np.fromiter((s.entropy for s in deep), dtype=np.float32)
    relaxed_peaks = acf_peaks(H, peak_min=NOPERIOD_B_RELAXED_PEAK_MIN)
    return "NOPERIOD-A" if not relaxed_peaks else "NOPERIOD-B?"


def format_peaks(peaks: list[tuple[int, float]]) -> str:
    if not peaks:
        return "[]"
    return "[" + ", ".join(f"({lag},{val:.2f})" for lag, val in peaks) + "]"


def main() -> None:
    manifest: dict[str, str] = {prefix: tag for prefix, tag in BATCH}

    conn = open_store(default_store_path())
    trajectory_ids = [
        tid for (tid,) in conn.execute(
            "SELECT trajectory_id FROM trajectories ORDER BY trajectory_id"
        ).fetchall()
    ]

    rows: list[dict] = []
    for tid in trajectory_ids:
        traj = read_trajectory(conn, tid)
        steps = traj.steps
        if len(steps) < DEEP_START + 256:
            continue
        deep = steps[DEEP_START:]
        H = np.fromiter((s.entropy for s in deep), dtype=np.float32)
        floor_H = float(np.median(H))
        osc_amp = float(H.std())
        H_iqr = (float(np.percentile(H, 25)), float(np.percentile(H, 75)))

        catalog_tag, peaks, period = catalog_regime_tag(steps)
        harmonic = harmonic_candidate(peaks)
        noperiod_sub = noperiod_cluster(steps) if catalog_tag == "NOPERIOD" else None
        manifest_tag = manifest.get(tid[:8])

        rows.append({
            "tid": tid,
            "catalog_tag": catalog_tag,
            "harmonic": harmonic,
            "noperiod_sub": noperiod_sub,
            "manifest_tag": manifest_tag,
            "peaks": peaks,
            "period": period,
            "floor_H": floor_H,
            "osc_amp": osc_amp,
            "H_iqr": H_iqr,
        })

    conn.close()

    tag_order = [
        "SLOTTED-CLASS",
        "SLOTTED-MIXED",
        "SLOTTED-COUNTER-INT",
        "SLOTTED-COUNTER-LETTER",
        "SCAFFOLD",
        "NOPERIOD",
    ]
    rows.sort(key=lambda r: (
        tag_order.index(r["catalog_tag"]) if r["catalog_tag"] in tag_order else len(tag_order),
        not r["harmonic"],
        r["noperiod_sub"] or "",
        r["tid"],
    ))

    # ---- header ----
    print(f"regime-tag audit — {len(rows)} trajectories with len(steps) >= {DEEP_START + 256}")
    print(f"deep window: [{DEEP_START}, end)")
    print()
    print("derived columns:")
    print(f"   catalog_tag: SLOTTED-CLASS / -MIXED / -COUNTER-INT / -COUNTER-LETTER / SCAFFOLD / NOPERIOD")
    print(f"                (period + slot-evidence rules from shape_catalog.py, inlined here)")
    print(f"   harmonic:    SLOTTED-HARMONIC candidate (first-cut predicate)")
    print(f"                len(peaks) >= {HARMONIC_MIN_PEAKS}, peaks[1..2] at integer multiples of")
    print(f"                peaks[0].lag within ±{HARMONIC_LAG_TOLERANCE} step")
    print(f"   noperiod_sub: NOPERIOD-A (no peaks at relaxed PEAK_MIN={NOPERIOD_B_RELAXED_PEAK_MIN})")
    print(f"                vs NOPERIOD-B? (peaks exist at relaxed but not default; '?' marks the")
    print(f"                bimodal-H half of the B definition as not yet operationalised)")
    print(f"   manifest:    tag from first_batch_branches.BATCH if present, else '—'")
    print()

    # ---- per-row table ----
    width = 110
    print("=" * width)
    print(f"{'tid':<10} {'catalog_tag':<24} {'H?':<4} {'np_sub':<13} {'manifest':<24} "
          f"{'period':>6} {'osc':>6} {'floorH':>7}")
    print("-" * width)
    for r in rows:
        h_flag = "✓" if r["harmonic"] else "·"
        np_sub = r["noperiod_sub"] or "—"
        manifest_tag = r["manifest_tag"] or "—"
        period_str = f"{r['period']}" if r["period"] is not None else "—"
        print(
            f"{r['tid'][:8]:<10} {r['catalog_tag']:<24} {h_flag:<4} {np_sub:<13} "
            f"{manifest_tag:<24} {period_str:>6} {r['osc_amp']:>6.3f} {r['floor_H']:>7.4f}"
        )
    print("=" * width)
    print()

    # ---- per-row peaks (for the harmonic candidates and NOPERIOD-B?s) ----
    print("peaks for SLOTTED-HARMONIC candidates and NOPERIOD-B? specimens:")
    for r in rows:
        if r["harmonic"] or r["noperiod_sub"] == "NOPERIOD-B?":
            note = []
            if r["harmonic"]:
                note.append("HARMONIC")
            if r["noperiod_sub"] == "NOPERIOD-B?":
                note.append("B?")
            print(f"   {r['tid'][:8]} ({'/'.join(note)}): peaks={format_peaks(r['peaks'])}  "
                  f"H_IQR=[{r['H_iqr'][0]:.3f}, {r['H_iqr'][1]:.3f}]")
    print()

    # ---- summary: counts ----
    print("counts by catalog_tag:")
    counts = Counter(r["catalog_tag"] for r in rows)
    for tag in tag_order:
        if counts[tag]:
            print(f"   {tag:25s} {counts[tag]:3d}")
    print()

    print("SLOTTED-HARMONIC candidates by catalog_tag (cross-tag overlap):")
    harm_by_tag: dict[str, int] = defaultdict(int)
    for r in rows:
        if r["harmonic"]:
            harm_by_tag[r["catalog_tag"]] += 1
    for tag in tag_order:
        if harm_by_tag[tag]:
            print(f"   {tag:25s} {harm_by_tag[tag]:3d}")
    if not harm_by_tag:
        print(f"   (none)")
    print()

    print("NOPERIOD sub-classification:")
    np_counts: Counter = Counter(r["noperiod_sub"] for r in rows if r["noperiod_sub"])
    for sub in ("NOPERIOD-A", "NOPERIOD-B?"):
        if np_counts[sub]:
            print(f"   {sub:25s} {np_counts[sub]:3d}")
    print()

    # ---- summary: manifest agreement ----
    # Manifest carries flat strings that conflate two orthogonal axes: slot-
    # character (CLASS / COUNTER / SCAFFOLD) and peak-structure (HARMONIC).
    # "SLOTTED-HARMONIC" in BATCH means "SLOTTED-* with harmonic peak ladder";
    # the audit comparison axis-matches rather than string-matches.
    def structured(row: dict) -> tuple[str, str | None, bool]:
        """Return (umbrella, slot_character, harmonic)."""
        if row["catalog_tag"] == "NOPERIOD":
            return ("NOPERIOD", row["noperiod_sub"].rstrip("?").split("-")[1], False)
        if row["catalog_tag"] == "SCAFFOLD":
            return ("SCAFFOLD", None, row["harmonic"])
        slot_char = row["catalog_tag"].removeprefix("SLOTTED-")
        return ("SLOTTED", slot_char, row["harmonic"])

    def manifest_axes(tag: str) -> tuple[str, str | None, bool | None]:
        """What axes does a manifest tag actually constrain?
        Returns (umbrella, slot_character_or_None, harmonic_or_None);
        None means the axis is unconstrained by the manifest."""
        if tag.startswith("NOPERIOD-"):
            return ("NOPERIOD", tag.split("-")[1], None)
        if tag == "SCAFFOLD":
            return ("SCAFFOLD", None, None)
        if tag == "SLOTTED-HARMONIC":
            return ("SLOTTED", None, True)  # slot character unconstrained
        if tag.startswith("SLOTTED-"):
            return ("SLOTTED", tag.removeprefix("SLOTTED-"), None)
        raise ValueError(f"unrecognised manifest tag {tag!r}")

    manifest_rows = [r for r in rows if r["manifest_tag"] is not None]
    print(f"manifest agreement ({len(manifest_rows)} entries from BATCH):")
    print(f"   match rule: axis-match. manifest axes that are None (unconstrained)")
    print(f"   pass on any derived value; constrained axes must equal derived.")
    print()

    agree = 0
    disagree: list[tuple[str, str, str]] = []
    for r in manifest_rows:
        m_umbrella, m_slot, m_harm = manifest_axes(r["manifest_tag"])
        d_umbrella, d_slot, d_harm = structured(r)
        derived_str = f"{d_umbrella}" + (f"-{d_slot}" if d_slot else "") + ("+H" if d_harm else "")
        ok = (d_umbrella == m_umbrella and
              (m_slot is None or m_slot == d_slot) and
              (m_harm is None or m_harm == d_harm))
        if ok:
            agree += 1
        else:
            disagree.append((r["tid"][:8], r["manifest_tag"], derived_str))

    print(f"   agreement: {agree}/{len(manifest_rows)}")
    if disagree:
        print(f"   disagreements:")
        for tid8, m, d in disagree:
            print(f"      {tid8}  manifest={m!r:<25} derived={d!r}")
    print()

    print("manifest-tag distribution (BATCH ground truth):")
    manifest_counts = Counter(r["manifest_tag"] for r in manifest_rows)
    for tag, n in sorted(manifest_counts.items()):
        print(f"   {tag:25s} {n:3d}")
    print()

    # ---- coverage gaps ----
    no_manifest = [r for r in rows if r["manifest_tag"] is None]
    print(f"coverage: {len(no_manifest)} trajectories have no manifest tag")
    print(f"   derived structured labels (umbrella, slot_character, harmonic):")
    structured_counts: Counter = Counter()
    for r in no_manifest:
        u, s, h = structured(r)
        key = f"{u}" + (f"-{s}" if s else "") + ("+H" if h else "")
        structured_counts[key] += 1
    for tag, n in sorted(structured_counts.items(), key=lambda x: -x[1]):
        print(f"      {tag:30s} {n:3d}")


if __name__ == "__main__":
    main()
