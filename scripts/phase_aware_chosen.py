"""Phase-aware chosen-token analysis — Cycle-2 forward-sequence move N1.

Read-only over `data/peirce.db`. For each of the 100 fp16 selection-bias
observations whose deep-window entropy has a detectable cycle period,
partition the deep window by phase position and compute chosen-token
entropy across recurrences at each phase.

Phases whose chosen-token Shannon entropy is above ε are *slots*: the
chosen token rotates across recurrences. The empirical alt-token
distribution at a slot reads out the model's local prior over the slot's
implicit class. Phases at zero chosen-entropy are *scaffolding*: the
chosen token is fixed across recurrences.

Per-trajectory catalog entry:

  * period (from autocorrelation of mean-subtracted deep-window H),
  * floor_H, osc_amp, num phases, num slots,
  * for each slot: position-in-cycle, recurrence count, empirical
    distribution of chosen tokens, empirical distribution of alt tokens.

Trajectories sorted by num_slots desc, then osc_amp desc — class-
enumeration specimens (slot count > 0) at the top, single-mode cycles
(slot count == 0) at the bottom. Trajectories with no detectable period
are tagged NOPERIOD and printed last.

This is the descriptive readout that re-derives the slot vs scaffolding
partition mechanically, without by-eye selection. The output is the
first attractor catalog under the slot/scaffolding decomposition. The
naming of regimes (whether per-trajectory tags map to the Cycle-1
R1/R2/R3 partition or to the renamed single-mode-cycle / single-mode-
template-cycle / class-enumeration-template-cycle vocabulary) follows in
a later doc move once this catalog has been read.

Read-only: no model load, no inference. Tokenizer-free. The full alt
distribution at slot positions is not persisted (only top-1 alt + its
probability), so the empirical alt distribution here is a top-1-alt
proxy; full-distribution slot-readout is downstream work that requires
inference.

Run via: uv run python scripts/phase_aware_chosen.py
"""
from __future__ import annotations

import json
from collections import Counter

import numpy as np

from peirce.runner import default_store_path
from peirce.store import open_store, read_observation


SELBIAS_PRED_NAMES = {"eos", "basin_capture", "window_cap"}
SELBIAS_BASIN_PARAMS = {"max_period": 32, "cycle_window": 256, "min_repetitions": 4}

DEEP_START = 1024
SLOT_H_EPS = 1e-3            # chosen-token H above this counts as non-degenerate
LAG_MIN, LAG_MAX = 2, 128    # autocorrelation search window (matches plot_trajectories)
PEAK_MIN = 0.3               # autocorrelation peak threshold
TOP_K_SLOT_DIST = 8          # how many tokens to print per slot distribution


def is_selection_bias_obs(predicates_json: str) -> bool:
    preds = json.loads(predicates_json)
    names = {p["name"] for p in preds}
    if names != SELBIAS_PRED_NAMES:
        return False
    for p in preds:
        if p["name"] == "basin_capture" and p["params"] != SELBIAS_BASIN_PARAMS:
            return False
    return True


def dominant_period(
    x: np.ndarray, lag_min: int = LAG_MIN, lag_max: int = LAG_MAX, peak_min: float = PEAK_MIN
) -> int | None:
    """Lag of the first significant autocorrelation peak in [lag_min, lag_max].

    Copy of `scripts/plot_trajectories.py:dominant_period`. Candidate for
    promotion to a `peirce/shape.py` module once a third consumer lands;
    duplicated here to keep N1 standalone.
    """
    if x.size < lag_max * 2:
        return None
    x = x - x.mean()
    if x.std() < 1e-4:
        return None
    n = x.size
    ac = np.correlate(x, x, mode="full")[n - 1:]
    if ac[0] <= 0:
        return None
    ac = ac / ac[0]
    region = ac[lag_min : lag_max + 1]
    if region.size == 0:
        return None
    idx = int(np.argmax(region))
    if region[idx] < peak_min:
        return None
    return lag_min + idx


def shannon_H_nats(counter: Counter) -> float:
    """Shannon entropy in nats of an empirical distribution given as a Counter."""
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


def main() -> None:
    conn = open_store(default_store_path())
    rows = conn.execute(
        "SELECT observation_id, predicates_json FROM observations"
    ).fetchall()

    items: list[dict] = []
    for oid, preds_json in rows:
        if not is_selection_bias_obs(preds_json):
            continue
        obs = read_observation(conn, oid)
        steps = obs.trajectory.steps
        if len(steps) < DEEP_START + LAG_MAX * 2:
            continue
        deep = steps[DEEP_START:]
        H = np.fromiter((s.entropy for s in deep), dtype=np.float32)
        period = dominant_period(H)
        floor_H = float(np.median(H))
        osc_amp = float(H.std())

        item: dict = {
            "oid": oid,
            "period": period,
            "floor_H": floor_H,
            "osc_amp": osc_amp,
            "num_phases": period,
            "num_slots": 0,
            "slots": [],   # list of {phase, n_recur, chosen_dist, alt_dist, chosen_H}
        }
        if period is None:
            items.append(item)
            continue

        # Partition deep-window positions by phase. Phase labels are
        # arbitrary (just `pos % period`); what matters is the slot/
        # scaffolding partition, which is invariant under relabeling.
        for phase in range(period):
            chosen_counter: Counter = Counter()
            alt_counter: Counter = Counter()
            for i in range(phase, len(deep), period):
                step = deep[i]
                chosen_counter[step.token] += 1
                alt_counter[step.alt_token] += 1
            chosen_H = shannon_H_nats(chosen_counter)
            if chosen_H > SLOT_H_EPS:
                item["slots"].append({
                    "phase": phase,
                    "n_recur": sum(chosen_counter.values()),
                    "chosen_H": chosen_H,
                    "chosen_dist": chosen_counter,
                    "alt_dist": alt_counter,
                })
        item["num_slots"] = len(item["slots"])
        items.append(item)

    # Sort: trajectories with detected period first, by num_slots desc,
    # then by osc_amp desc; NOPERIOD trajectories last.
    def sort_key(it: dict) -> tuple:
        has_period = it["period"] is not None
        return (0 if has_period else 1, -it["num_slots"], -it["osc_amp"])

    items.sort(key=sort_key)

    n_total = len(items)
    n_no_period = sum(1 for it in items if it["period"] is None)
    n_with_slots = sum(1 for it in items if it["num_slots"] > 0)
    n_scaffold_only = n_total - n_no_period - n_with_slots

    print(f"selection-bias observations: {n_total}")
    print(f"deep window: [{DEEP_START}, end)")
    print(f"period detection: lag ∈ [{LAG_MIN}, {LAG_MAX}], peak ≥ {PEAK_MIN}")
    print(f"slot threshold: chosen-token H > {SLOT_H_EPS} nats")
    print()
    print(f"  trajectories with detected period:           {n_total - n_no_period}/{n_total}")
    print(f"     of those, with at least one slot:         {n_with_slots}")
    print(f"     of those, scaffolding-only (no slots):    {n_scaffold_only}")
    print(f"  trajectories with no detected period:        {n_no_period}")
    print()

    for it in items:
        if it["period"] is None:
            print(
                f"[NOPERIOD ]  {it['oid'][:8]}  "
                f"floor_H={it['floor_H']:.4f}  osc_amp={it['osc_amp']:.4f}  "
                f"(deep-window variance below noise or no autocorrelation peak)"
            )
            continue
        if it["num_slots"] == 0:
            tag = "SCAFFOLD "
        else:
            tag = "SLOTTED  "
        print(
            f"[{tag}]  {it['oid'][:8]}  period={it['period']:3d}  "
            f"floor_H={it['floor_H']:.4f}  osc_amp={it['osc_amp']:.4f}  "
            f"slots={it['num_slots']}/{it['num_phases']}"
        )
        for slot in it["slots"]:
            print(
                f"   phase={slot['phase']:3d}  n_recur={slot['n_recur']:3d}  "
                f"chosen_H={slot['chosen_H']:.3f}"
            )
            print(f"      chosen: {format_distribution(slot['chosen_dist'])}")
            print(f"      alt:    {format_distribution(slot['alt_dist'])}")
        print()

    conn.close()


if __name__ == "__main__":
    main()
