"""Trajectory and per-step record dataclasses.

Per design-reqs v2.1, each step of a trajectory carries five fields: the
chosen token (id and decoded), its log-probability, the distribution
entropy, and the second-most-likely token of the distribution (id, decoded,
probability). The trajectory bundles the initial token ids, the per-step
records, and the terminal-event tag.

The top-2 fields report literal rank-2 of the distribution, independent of
which token was chosen. For T=0 argmax steps (everything past a possible
step-0 override), chosen equals rank-1 and top-2 is the natural escape
candidate. At step 0 with first_step_override picking a non-argmax token,
the top-2 field can coincide with chosen (when the override picks rank-2)
or be unrelated to escape pressure relative to chosen (other ranks).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StepRecord:
    token_id: int
    token: str
    log_prob: float
    entropy: float
    top2_token_id: int
    top2_token: str
    top2_prob: float


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
