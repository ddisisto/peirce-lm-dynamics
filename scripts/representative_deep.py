"""Read-only renderer for representative-deep candidates.

No inference. Reads the long-lived store and re-presents the L_arch-budget
observation for selected branches from the broad-shallow ensemble.
Originally this script re-ran a handful of candidates at L_arch to
adjudicate whether their broad-shallow cycles held under the runtime
predicate; the selection_bias run now does that for all 100 trajectories,
so this script's job is reduced to surfacing the same per-candidate report
by reading what selection_bias wrote.

Selections are keyed by chosen_id (the BOS-top-K branch token), not by
rank — created_at on trajectory rows is second-precision, so rank-by-
insertion is not stable when multiple branches insert in the same second.
chosen_id is the branch's persistent identity in the store.

The latest observation per trajectory (highest observed_length) is the
selection_bias one when present, otherwise the broad_shallow budget=64 one.

Run via: uv run python scripts/representative_deep.py
"""
from __future__ import annotations

from transformers import AutoTokenizer

from peirce.basins import detect_tail_cycle
from peirce.records import Observation
from peirce.runner import default_store_path
from peirce.store import open_store, read_observation

MODEL_ID = "EleutherAI/pythia-1b-deduped"
MAX_CYCLE_PERIOD = 32
CYCLE_WINDOW = 256
STATS_WINDOW = 256

SELECTED = [
    (187,   "argmax of BOS ('\\n') — escaped whitespace immediately"),
    (50268, "10-space branch — broad-shallow cyc=4 (table fence)"),
    (50267, "11-space branch — broad-shallow cyc=1 (pure space + |)"),
    (50271, "7-space branch — broad-shallow cyc=2 (pipe-bar)"),
    (50254, "24-space branch — broad-shallow cyc=1 (pure space)"),
    (64,    "'_' branch — broad-shallow cyc=9 (semantic phrase)"),
]


def window_stats(values: list[float], n: int) -> tuple[float, float]:
    n = min(n, len(values))
    return sum(values[:n]) / n, sum(values[-n:]) / n


def latest_observation(conn, trajectory_id: str) -> Observation | None:
    """Return the observation with the largest observed_length for this trajectory."""
    row = conn.execute(
        """SELECT observation_id FROM observations
           WHERE trajectory_id = ?
           ORDER BY observed_length DESC, created_at DESC LIMIT 1""",
        (trajectory_id,),
    ).fetchone()
    if row is None:
        return None
    return read_observation(conn, row[0])


def trajectory_id_for_chosen_id(conn, chosen_id: int) -> str | None:
    injections_json = f'[{{"chosen_id":{chosen_id},"position":0}}]'
    row = conn.execute(
        "SELECT trajectory_id FROM trajectories WHERE injections_json = ?",
        (injections_json,),
    ).fetchone()
    return row[0] if row else None


def main() -> None:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    store_path = default_store_path()
    conn = open_store(store_path)

    n_trajectories = conn.execute("SELECT COUNT(*) FROM trajectories").fetchone()[0]

    print(f"Store: {store_path}")
    print(f"Trajectories in store: {n_trajectories}")
    print(
        f"basin probe: max_period={MAX_CYCLE_PERIOD} "
        f"cycle_window={CYCLE_WINDOW} stats_window={STATS_WINDOW}\n"
    )

    for chosen_id, narrative in SELECTED:
        branch = tokenizer.decode([chosen_id])
        tid = trajectory_id_for_chosen_id(conn, chosen_id)
        if tid is None:
            print(f"[id={chosen_id:5d}] {branch!r} — {narrative}")
            print("  (trajectory not present in store)\n")
            continue
        obs = latest_observation(conn, tid)
        if obs is None:
            print(f"[id={chosen_id:5d}] {branch!r} — {narrative}")
            print("  (no observation recorded)\n")
            continue

        print(f"[id={chosen_id:5d}] {branch!r} — {narrative}")
        print(f"  terminal: {obs.terminal_event}, length: {obs.length}")

        log_probs = [s.log_prob for s in obs.steps]
        entropies = [s.entropy for s in obs.steps]
        alt_probs = [s.alt_prob for s in obs.steps]
        lp_early, lp_late = window_stats(log_probs, 64)
        H_early, H_late = window_stats(entropies, 64)
        ap_early, ap_late = window_stats(alt_probs, 64)

        if obs.terminal_event == "candidate-basin":
            sig = detect_tail_cycle(
                obs.steps,
                max_period=MAX_CYCLE_PERIOD,
                cycle_window=CYCLE_WINDOW,
                stats_window=STATS_WINDOW,
            )
            cycle_text_clean = sig.cycle_text.replace("\n", "\\n").replace("\t", "\\t")
            print(
                f"  basin: period={sig.period} reps={sig.repetitions_in_cycle_window} "
                f"H={sig.late_window_mean_entropy:.3f} "
                f"gap={sig.late_window_mean_logit_gap:.3f}"
            )
            print(f"    cycle text: {cycle_text_clean!r}")
            print(f"    cycle token-ids: {sig.cycle_token_ids}")
        else:
            token_ids = [s.token_id for s in obs.steps]
            tail = token_ids[-128:] if len(token_ids) >= 128 else token_ids
            last_text = tokenizer.decode(tail).replace("\n", "\\n").replace("\t", "\\t")
            if len(last_text) > 400:
                last_text = last_text[:397] + "..."
            print(f"  last 128 tokens decoded: {last_text}")

        print(f"  log_prob  early avg={lp_early:7.3f}  late avg={lp_late:7.3f}")
        print(f"  entropy   early avg={H_early:.3f}    late avg={H_late:.3f}")
        print(f"  alt_prob  early avg={ap_early:.3f}    late avg={ap_late:.3f}")
        print()


if __name__ == "__main__":
    main()
