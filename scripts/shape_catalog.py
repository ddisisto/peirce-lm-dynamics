"""Shape catalog under v0.2 vocabulary — Cycle-2 forward-sequence move N1.5.

Read-only over `data/peirce.db`. The consolidated descriptive readout of
the 100-trajectory substrate, partitioned by N1's slot / scaffold /
no-period decomposition and extended along three axes:

  (a) Period detection via `peirce.shape.acf_peaks`. The full
      autocorrelation peak list is the underlying measurement and is
      reported per trajectory in the `peaks=` field of every row; harmonic
      ladders show as multiple entries at multiples of the fundamental,
      multi-period or sub-period structure shows as non-multiple lags,
      NOPERIOD signals show `[]`. `dominant_period` is the single-int
      convention layer over `peaks` (smallest in-list divisor of the
      strongest peak; falls back to the strongest peak); convention is
      revisable, and specimens where the convention's choice looks
      questionable can be audited by inspecting `peaks` directly.

  (b) Counter-vs-class slot tagging. For each slot, the chosen-token
      sequence in recurrence order is tested for arithmetic structure:
      successive int-deltas (median + match-fraction) and successive
      letter-ord-deltas. A slot tags `COUNTER-INT` / `COUNTER-LETTER`
      when the median delta is ±1 and the match fraction crosses
      `COUNTER_MATCH_THRESHOLD`; otherwise `CLASS`. The slot-readout
      *operation* (alt-token distribution at the slot phase) is the same
      in all three; the *interpretation* differs sharply. With current
      sample (4 counter / 1 class specimens at first light) the heuristic
      describes rather than classifies — both the tag and the underlying
      delta evidence are reported per slot.

  (c) Position-resolved `logit_gap` and `gap_over_H` readouts. Per-step
      `gap_over_H = logit_gap / max(entropy, GAP_OVER_H_EPS)` is computed
      then aggregated by phase (for periodic trajectories) or summarised
      over the deep window (for NOPERIOD). Surfaces commitment-strength
      heterogeneity within SCAFFOLD-only and gives a principled candidate-
      list for N2: positions where the model's commitment is weakest
      relative to its residual uncertainty are the natural perturbation
      candidates.

Output is a single stdout report. Rows grouped by tag (SLOTTED-COUNTER /
SLOTTED-CLASS / SCAFFOLD / NOPERIOD), within group sorted by descending
`osc_amp`. Aggregate sections at the end: counts by tag, top-K positions
by lowest `gap_over_H` (the principled N2 candidate list), top-K by
highest entropy (the simplest baseline).

Read-only: no model load, no inference. Tokenizer-free (relies on the
decoded `token` / `alt_token` fields persisted in `step_records`). The
empirical alt distributions are top-1-alt only, since the persisted
record carries one alt per step; full-distribution slot-readout is
inference-side work, not catalog scope.

Run via: uv run python scripts/shape_catalog.py
"""
from __future__ import annotations

import json
from collections import Counter

import numpy as np

from peirce.runner import default_store_path
from peirce.shape import DEEP_START, LAG_MAX, LAG_MIN, PEAK_MIN, acf_peaks, dominant_period
from peirce.store import open_store, read_observation


SELBIAS_PRED_NAMES = {"eos", "basin_capture", "window_cap"}
SELBIAS_BASIN_PARAMS = {"max_period": 32, "cycle_window": 256, "min_repetitions": 4}

SLOT_H_EPS = 1e-3
TOP_K_SLOT_DIST = 8
TOP_K_CANDIDATE = 20
COUNTER_MATCH_THRESHOLD = 0.75
GAP_OVER_H_EPS = 1e-4
SCAFFOLD_PHASES_TO_SHOW = 3   # top-K extreme phases to print per SCAFFOLD specimen


def is_selection_bias_obs(predicates_json: str) -> bool:
    preds = json.loads(predicates_json)
    names = {p["name"] for p in preds}
    if names != SELBIAS_PRED_NAMES:
        return False
    for p in preds:
        if p["name"] == "basin_capture" and p["params"] != SELBIAS_BASIN_PARAMS:
            return False
    return True


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


def render_token(t: str) -> str:
    return t.replace("\n", "\\n").replace("\t", "\\t")


def format_distribution(counter: Counter, top_k: int = TOP_K_SLOT_DIST) -> str:
    total = sum(counter.values())
    items = counter.most_common(top_k)
    pieces = []
    for tok, c in items:
        frac = c / total
        pieces.append(f"{render_token(tok)!r}×{c}({frac:.2f})")
    if len(counter) > top_k:
        pieces.append(f"+{len(counter) - top_k} more")
    return " ".join(pieces)


def format_peaks(peaks: list[tuple[int, float]]) -> str:
    if not peaks:
        return "[]"
    return "[" + ", ".join(f"({lag},{val:.2f})" for lag, val in peaks) + "]"


def slot_chosen_evidence(chosen_seq: list[str]) -> dict:
    """Test a slot's chosen-token sequence for counter (consecutive
    integers / alphabet letters) vs class structure.

    Returns a dict carrying the underlying delta evidence (median +
    match-fraction for int and letter readings) and the convention-tag
    derived from it. Reporting both keeps the tag honest at small
    sample size: with N=4 known counters / N=1 known class as of N1
    first-light, the convention is a description aid, not a classifier.
    """
    stripped = [t.strip() for t in chosen_seq]
    n_pairs = max(0, len(stripped) - 1)

    # int reading
    int_med: int | None = None
    int_frac: float = 0.0
    try:
        ints = [int(t) for t in stripped]
        if n_pairs > 0:
            deltas = np.diff(np.asarray(ints))
            med = int(np.median(deltas))
            int_med = med
            int_frac = float(np.mean(deltas == med))
    except (ValueError, TypeError):
        pass

    # single-letter reading
    letter_med: int | None = None
    letter_frac: float = 0.0
    if all(len(t) == 1 and t.isascii() and t.isalpha() for t in stripped):
        if n_pairs > 0:
            ords = np.asarray([ord(t) for t in stripped])
            deltas = np.diff(ords)
            med = int(np.median(deltas))
            letter_med = med
            letter_frac = float(np.mean(deltas == med))

    if int_med in (1, -1) and int_frac >= COUNTER_MATCH_THRESHOLD:
        tag = "COUNTER-INT"
    elif letter_med in (1, -1) and letter_frac >= COUNTER_MATCH_THRESHOLD:
        tag = "COUNTER-LETTER"
    else:
        tag = "CLASS"

    return {
        "int_median": int_med,
        "int_match_frac": int_frac,
        "letter_median": letter_med,
        "letter_match_frac": letter_frac,
        "tag": tag,
    }


def format_evidence(ev: dict) -> str:
    int_med = ev["int_median"]
    let_med = ev["letter_median"]
    int_str = "N/A" if int_med is None else f"median={int_med:+d} frac={ev['int_match_frac']:.2f}"
    let_str = "N/A" if let_med is None else f"median={let_med:+d} frac={ev['letter_match_frac']:.2f}"
    return f"int({int_str}) letter({let_str})"


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


def format_quartile(q: dict, fmt: str = ".3f") -> str:
    return f"median={q['median']:{fmt}} IQR=[{q['q1']:{fmt}}, {q['q3']:{fmt}}] min={q['min']:{fmt}} max={q['max']:{fmt}}"


def main() -> None:
    conn = open_store(default_store_path())
    rows = conn.execute(
        "SELECT observation_id, predicates_json FROM observations"
    ).fetchall()

    items: list[dict] = []
    candidates: list[dict] = []   # all deep-window positions across all trajectories
    h_baseline: list[dict] = []   # same, for highest-H baseline

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
        gap_over_H_step = gap / np.maximum(H, GAP_OVER_H_EPS)

        peaks = acf_peaks(H)
        period = dominant_period(H)
        floor_H = float(np.median(H))
        floor_gap = float(np.median(gap))
        osc_amp = float(H.std())
        gap_over_H = floor_gap / max(floor_H, GAP_OVER_H_EPS)

        item: dict = {
            "oid": oid,
            "peaks": peaks,
            "period": period,
            "floor_H": floor_H,
            "floor_gap": floor_gap,
            "osc_amp": osc_amp,
            "gap_over_H": gap_over_H,
            "num_phases": period,
            "slots": [],
            "scaffold_phase_stats": None,   # set for SCAFFOLD trajectories
            "noperiod_stats": None,         # set for NOPERIOD trajectories
        }

        if period is None:
            item["noperiod_stats"] = {
                "gap": quartile_summary(gap),
                "gap_over_H": quartile_summary(gap_over_H_step),
                "H": quartile_summary(H),
            }
            item["tag"] = "NOPERIOD"
            items.append(item)
        else:
            # Partition deep-window positions by phase.
            phase_stats = []
            for phase in range(period):
                idxs = np.arange(phase, len(deep), period)
                if idxs.size == 0:
                    continue
                chosen_counter: Counter = Counter()
                alt_counter: Counter = Counter()
                chosen_seq: list[str] = []
                for i in idxs:
                    step = deep[int(i)]
                    chosen_counter[step.token] += 1
                    alt_counter[step.alt_token] += 1
                    chosen_seq.append(step.token)
                chosen_H = shannon_H_nats(chosen_counter)
                phase_gap = gap[idxs]
                phase_goh = gap_over_H_step[idxs]
                phase_stats.append({
                    "phase": phase,
                    "n_recur": int(idxs.size),
                    "chosen_H": chosen_H,
                    "chosen_dist": chosen_counter,
                    "alt_dist": alt_counter,
                    "chosen_seq": chosen_seq,
                    "gap": quartile_summary(phase_gap),
                    "gap_over_H": quartile_summary(phase_goh),
                })
                if chosen_H > SLOT_H_EPS:
                    ev = slot_chosen_evidence(chosen_seq)
                    item["slots"].append({**phase_stats[-1], "evidence": ev})

            if item["slots"]:
                tags = {s["evidence"]["tag"] for s in item["slots"]}
                if tags == {"COUNTER-INT"}:
                    item["tag"] = "SLOTTED-COUNTER-INT"
                elif tags == {"COUNTER-LETTER"}:
                    item["tag"] = "SLOTTED-COUNTER-LETTER"
                elif tags == {"CLASS"}:
                    item["tag"] = "SLOTTED-CLASS"
                else:
                    item["tag"] = "SLOTTED-MIXED"
            else:
                item["tag"] = "SCAFFOLD"
                # rank phases by gap median; report top-K extremes
                phase_stats_sorted = sorted(phase_stats, key=lambda p: p["gap"]["median"])
                item["scaffold_phase_stats"] = {
                    "lowest": phase_stats_sorted[:SCAFFOLD_PHASES_TO_SHOW],
                    "highest": phase_stats_sorted[-SCAFFOLD_PHASES_TO_SHOW:][::-1],
                }
            items.append(item)

        # Candidate enumeration (all deep-window positions).
        for k, step in enumerate(deep):
            abs_idx = DEEP_START + k
            cand = {
                "oid": oid,
                "step_idx": abs_idx,
                "chosen": step.token,
                "alt": step.alt_token,
                "H": float(H[k]),
                "gap": float(gap[k]),
                "gap_over_H": float(gap_over_H_step[k]),
            }
            candidates.append(cand)
            h_baseline.append(cand)

    conn.close()

    # ---- ordering ----
    tag_order = [
        "SLOTTED-CLASS",
        "SLOTTED-MIXED",
        "SLOTTED-COUNTER-INT",
        "SLOTTED-COUNTER-LETTER",
        "SCAFFOLD",
        "NOPERIOD",
    ]
    def sort_key(it: dict) -> tuple:
        tag_idx = tag_order.index(it["tag"]) if it["tag"] in tag_order else len(tag_order)
        return (tag_idx, -it["osc_amp"])
    items.sort(key=sort_key)

    counts = Counter(it["tag"] for it in items)
    n_total = len(items)

    # ---- header ----
    print(f"shape catalog under v0.2 vocabulary — {n_total} fp16 selection-bias trajectories")
    print(f"deep window: [{DEEP_START}, end)")
    print()
    print("measurements (underlying):")
    print(f"   acf_peaks: local maxima of normalized acf in lag ∈ [{LAG_MIN}, {LAG_MAX}], "
          f"value ≥ {PEAK_MIN}")
    print(f"   chosen_H per phase: Shannon entropy (nats) of chosen tokens across recurrences")
    print(f"   gap_over_H per step: logit_gap / max(entropy, {GAP_OVER_H_EPS})")
    print()
    print("conventions (revisable; underlying measurements above):")
    print(f"   period:           smallest in-list divisor of the strongest peak in `peaks`")
    print(f"   slot:             chosen_H > {SLOT_H_EPS} nats at phase position")
    print(f"   counter heuristic: int / letter consecutivity at match-fraction ≥ {COUNTER_MATCH_THRESHOLD}")
    print()
    print("audit notes:")
    print(f"   period choice questionable? inspect `peaks=` field on the row")
    print(f"   slot/scaffold borderline?   chosen_H is reported per phase")
    print(f"   counter tag confidence?     int/letter delta evidence printed under each slot")
    print(f"   NOPERIOD specimens may have weak periods just below peak threshold")
    print()
    print("counts by tag:")
    for tag in tag_order:
        if counts[tag]:
            print(f"   {tag:25s} {counts[tag]:3d}")
    print()

    # ---- per-trajectory rows ----
    for it in items:
        oid_short = it["oid"][:8]
        peaks_str = format_peaks(it["peaks"])
        if it["tag"] == "NOPERIOD":
            print(f"[{it['tag']:24s}]  {oid_short}  peaks={peaks_str}  "
                  f"floor_H={it['floor_H']:.4f}  floor_gap={it['floor_gap']:.3f}  "
                  f"gap_over_H={it['gap_over_H']:.1f}  osc_amp={it['osc_amp']:.4f}")
            ns = it["noperiod_stats"]
            print(f"   deep H:          {format_quartile(ns['H'], '.4f')}")
            print(f"   deep gap:        {format_quartile(ns['gap'], '.3f')}")
            print(f"   deep gap_over_H: {format_quartile(ns['gap_over_H'], '.1f')}")
            print()
            continue

        period = it["period"]
        print(f"[{it['tag']:24s}]  {oid_short}  period={period:3d}  peaks={peaks_str}  "
              f"floor_H={it['floor_H']:.4f}  floor_gap={it['floor_gap']:.3f}  "
              f"gap_over_H={it['gap_over_H']:.1f}  osc_amp={it['osc_amp']:.4f}  "
              f"slots={len(it['slots'])}/{it['num_phases']}")

        for slot in it["slots"]:
            ev = slot["evidence"]
            print(f"   slot phase={slot['phase']:3d}  n_recur={slot['n_recur']:3d}  "
                  f"chosen_H={slot['chosen_H']:.3f}  tag={ev['tag']}")
            print(f"      chosen: {format_distribution(slot['chosen_dist'])}")
            print(f"      alt:    {format_distribution(slot['alt_dist'])}")
            print(f"      delta:  {format_evidence(ev)}")
            print(f"      gap:        {format_quartile(slot['gap'], '.3f')}")
            print(f"      gap_over_H: {format_quartile(slot['gap_over_H'], '.1f')}")

        if it["tag"] == "SCAFFOLD" and it["scaffold_phase_stats"]:
            sps = it["scaffold_phase_stats"]
            print(f"   phase-resolved gap (top-{SCAFFOLD_PHASES_TO_SHOW} lowest-gap phases):")
            for p in sps["lowest"]:
                print(f"      phase={p['phase']:3d}  "
                      f"gap_med={p['gap']['median']:.3f}  "
                      f"gap_over_H_med={p['gap_over_H']['median']:.1f}  "
                      f"chosen={render_token(next(iter(p['chosen_dist'])))!r}")
            print(f"   phase-resolved gap (top-{SCAFFOLD_PHASES_TO_SHOW} highest-gap phases):")
            for p in sps["highest"]:
                print(f"      phase={p['phase']:3d}  "
                      f"gap_med={p['gap']['median']:.3f}  "
                      f"gap_over_H_med={p['gap_over_H']['median']:.1f}  "
                      f"chosen={render_token(next(iter(p['chosen_dist'])))!r}")
        print()

    # ---- aggregate candidate-list section ----
    candidates.sort(key=lambda c: c["gap_over_H"])
    h_baseline.sort(key=lambda c: -c["H"])

    print("=" * 78)
    print(f"Top-{TOP_K_CANDIDATE} candidate positions by lowest gap_over_H "
          f"(principled N2 candidates):")
    print("=" * 78)
    for c in candidates[:TOP_K_CANDIDATE]:
        print(f"   {c['oid'][:8]}  step={c['step_idx']:5d}  "
              f"H={c['H']:.4f}  gap={c['gap']:.3f}  gap_over_H={c['gap_over_H']:.1f}  "
              f"chosen={render_token(c['chosen'])!r}  alt={render_token(c['alt'])!r}")
    print()
    print("=" * 78)
    print(f"Top-{TOP_K_CANDIDATE} candidate positions by highest H (baseline):")
    print("=" * 78)
    for c in h_baseline[:TOP_K_CANDIDATE]:
        print(f"   {c['oid'][:8]}  step={c['step_idx']:5d}  "
              f"H={c['H']:.4f}  gap={c['gap']:.3f}  gap_over_H={c['gap_over_H']:.1f}  "
              f"chosen={render_token(c['chosen'])!r}  alt={render_token(c['alt'])!r}")


if __name__ == "__main__":
    main()
