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

from .records import Trajectory


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


def detect_tail_cycle(
    trajectory: Trajectory,
    max_period: int = 32,
    cycle_window: int = 256,
    stats_window: int = 256,
) -> BasinSignature | None:
    """Detect a tail cycle in trajectory and return its signature.

    Looks for the smallest period p (1 <= p <= max_period) such that the last
    p tokens of the trajectory equal the p tokens immediately preceding them,
    within the last `cycle_window` tokens. If found, returns a BasinSignature
    including cycle content (token ids and decoded text) and late-window
    certainty stats over the last `stats_window` steps.

    Returns None if no cycle detected within max_period over the cycle window.
    """
    steps = trajectory.steps
    n = len(steps)
    if n < 2:
        return None

    tail = steps[-cycle_window:] if n > cycle_window else steps
    tail_ids = [s.token_id for s in tail]
    tail_n = len(tail_ids)

    period: int | None = None
    for p in range(1, min(max_period, tail_n // 2) + 1):
        if tail_ids[-p:] == tail_ids[-2 * p : -p]:
            period = p
            break

    if period is None:
        return None

    cycle_steps = tail[-period:]
    cycle_token_ids = tuple(s.token_id for s in cycle_steps)
    cycle_text = "".join(s.token for s in cycle_steps)
    repetitions = tail_n // period

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
