"""Basin detection probes.

Per design-reqs-records.md, probes are functions over a window of records that
produce a structured result. Basin detection probes specifically look for
evidence that a trajectory has entered a stable basin under hard-cap T=0.

This module implements basin detection v1 — tail cycle-period detection plus
late-window certainty stats for adjudication. The signature combines
*structural identification* (cycle period and content) with the *adjudication
signal* (late-window probability dynamics) that distinguishes a true asymptotic
basin from an extended transient.

Out of scope for v1: entropy-floor / logit-gap-floor detection that would catch
ascending sequences, ordinal cascades, and other non-cyclical local-success
traps. Threshold calibration for those probes needs the v1 catalog as a
reference distribution; see ideas.md "EOS as implicit-success signal" entry,
"local-success traps" subsection, for the broader context.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from .predicates import Predicate
from .records import StepRecord


@dataclass
class BasinSignature:
    """Structural fingerprint plus adjudication signal for an observed basin.

    Period and cycle content identify the basin (cycle_token_ids is the
    canonical hashable identity; cycle_text is human-readable). Late-window
    certainty stats are the adjudication signal: a true asymptotic basin
    has mean_log_prob → 0, mean_entropy → 0, mean_alt_prob → 0, and
    mean_logit_gap growing large; an extended transient retains elevated
    metrics on these axes as depth grows.
    """
    period: int
    cycle_token_ids: tuple[int, ...]
    cycle_text: str
    repetitions_in_cycle_window: int
    trajectory_length: int
    late_window_size: int
    late_window_mean_log_prob: float
    late_window_mean_entropy: float
    late_window_mean_alt_prob: float
    late_window_mean_logit_gap: float


def find_tail_cycle_period(
    token_ids: list[int],
    max_period: int = 32,
    cycle_window: int = 256,
) -> tuple[int, int] | None:
    """Structural-only counterpart of detect_tail_cycle: returns (period, reps).

    Operates directly on a list of ints, skipping decode and late-window
    statistics. Used by the runtime predicate, where only structural
    confirmation is needed at every step; the full BasinSignature with
    cycle text and adjudication stats is built once at termination via
    detect_tail_cycle. Saves ~4× mean()-over-256 plus tuple/string
    construction on every call.
    """
    n = len(token_ids)
    if n < 2:
        return None

    tail = token_ids[-cycle_window:] if n > cycle_window else token_ids
    tail_n = len(tail)

    period: int | None = None
    for p in range(1, min(max_period, tail_n // 2) + 1):
        if tail[-p:] == tail[-2 * p : -p]:
            period = p
            break

    if period is None:
        return None

    cycle = tail[-period:]
    repetitions = 1
    pos = tail_n - period
    while pos >= period and tail[pos - period:pos] == cycle:
        repetitions += 1
        pos -= period

    return period, repetitions


def detect_tail_cycle(
    steps: list[StepRecord],
    max_period: int = 32,
    cycle_window: int = 256,
    stats_window: int = 256,
) -> BasinSignature | None:
    """Detect a tail cycle in a step-record sequence and return its signature.

    Looks for the smallest period p (1 <= p <= max_period) such that the last
    p tokens of `steps` equal the p tokens immediately preceding them, within
    the last `cycle_window` tokens. If found, returns a BasinSignature
    including cycle content (token ids and decoded text) and late-window
    certainty stats over the last `stats_window` steps.

    Returns None if no cycle detected within max_period over the cycle window.
    """
    n = len(steps)
    if n < 2:
        return None

    token_ids = [s.token_id for s in steps]
    found = find_tail_cycle_period(token_ids, max_period, cycle_window)
    if found is None:
        return None
    period, repetitions = found

    tail = steps[-cycle_window:] if n > cycle_window else steps
    cycle_steps = tail[-period:]
    cycle_token_ids = tuple(s.token_id for s in cycle_steps)
    cycle_text = "".join(s.token for s in cycle_steps)

    stats_steps = steps[-stats_window:] if n > stats_window else steps
    sw_size = len(stats_steps)

    return BasinSignature(
        period=period,
        cycle_token_ids=cycle_token_ids,
        cycle_text=cycle_text,
        repetitions_in_cycle_window=repetitions,
        trajectory_length=n,
        late_window_size=sw_size,
        late_window_mean_log_prob=mean(s.log_prob for s in stats_steps),
        late_window_mean_entropy=mean(s.entropy for s in stats_steps),
        late_window_mean_alt_prob=mean(s.alt_prob for s in stats_steps),
        late_window_mean_logit_gap=mean(s.logit_gap for s in stats_steps),
    )


def basin_capture_predicate(
    max_period: int = 32,
    cycle_window: int = 256,
    min_repetitions: int = 4,
) -> Predicate:
    """Predicate that terminates on a tail-cycle confirmed for `min_repetitions` reps.

    Probes every step once n_steps >= min_repetitions, calling the
    structural-only find_tail_cycle_period helper (decoded text and
    late-window stats are not needed at the predicate gate). Tag emitted
    is `candidate-basin`, matching the intrinsic terminal-event vocabulary.

    `min_repetitions` is the confirmation threshold: structural detection
    fires at 2 reps (last-p == prev-p), but at K=2 the runtime probe is
    too permissive — many trajectories transit through brief recurrences
    en route to a different asymptotic attractor and would be captured
    prematurely. K=4 (default) matches the empirical distribution of the
    v1 broad-shallow catalog (every entry had 4+ reps when measured at
    depth 64). Late-window stats remain the adjudication signal for
    crystal vs extended-transient classification, computed post-hoc from
    the truncated trajectory via detect_tail_cycle.
    """
    def check(history: list[int], records: list[StepRecord], n_steps: int) -> str | None:
        if n_steps < min_repetitions:
            return None
        # Bound to cycle_window to avoid materializing a multi-thousand-elt
        # slice each step at long depth; min(n_steps, ...) keeps initial_ids
        # out of the early-step view.
        token_ids = history[-min(n_steps, cycle_window):]
        found = find_tail_cycle_period(token_ids, max_period, cycle_window)
        if found is None or found[1] < min_repetitions:
            return None
        return "candidate-basin"
    return check
