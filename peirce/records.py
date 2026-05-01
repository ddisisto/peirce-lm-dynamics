"""Trajectory and per-step record dataclasses.

Per design-reqs-records.md, each step of a trajectory carries the chosen
token (id and decoded), its log-probability, the distribution entropy,
the most-probable non-chosen alternative (id, decoded, probability), and
the rank-1/rank-2 logit gap. The trajectory bundles the initial token
ids, the per-step records, and the terminal-event tag.

The alt fields always identify the dominant alternative to chosen. At T=0
argmax steps the alternative is rank-2 of the distribution and the pair
(log_prob, alt_prob) measures escape pressure. At step-0 override or T>0
sampled steps the alternative is rank-1 (the model's argmax preference)
and the pair measures divergence between trajectory and model intent.

The logit_gap is the rank-1 minus rank-2 log-probability (equivalently,
the rank-1 minus rank-2 logit, since softmax shifts both by the same
per-step constant). It is the numerical-noise margin: cross-system
argmax disagreement at this step is plausible when logit_gap falls below
the producing stack's effective floating-point noise floor (typically
~1e-3 to ~1e-4 in fp32, larger in lower precision).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StepRecord:
    token_id: int
    token: str
    log_prob: float
    entropy: float
    alt_token_id: int
    alt_token: str
    alt_prob: float
    logit_gap: float


@dataclass
class Trajectory:
    initial_ids: list[int]
    steps: list[StepRecord]
    terminal_event: str

    @property
    def token_ids(self) -> list[int]:
        return [*self.initial_ids, *(s.token_id for s in self.steps)]

    @property
    def length(self) -> int:
        return len(self.steps)
