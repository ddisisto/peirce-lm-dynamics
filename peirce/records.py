"""Trajectory and per-step record dataclasses.

Per design-reqs v2.2, each step of a trajectory carries five fields: the
chosen token (id and decoded), its log-probability, the distribution
entropy, and the most-probable non-chosen alternative (id, decoded,
probability). The trajectory bundles the initial token ids, the per-step
records, and the terminal-event tag.

The alt fields always identify the dominant alternative to chosen. At T=0
argmax steps the alternative is rank-2 of the distribution and the pair
(log_prob, alt_prob) measures escape pressure. At step-0 override or T>0
sampled steps the alternative is rank-1 (the model's argmax preference)
and the pair measures divergence between trajectory and model intent.
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
