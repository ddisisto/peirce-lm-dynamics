"""Trajectory packet and per-step record dataclasses.

Per design-reqs-records.md, a Trajectory IS the observation packet — the
citable unit. It carries stack identity, initial condition, predicate set,
inference strategy, the per-step thin records (canonical layer), the
rank-event log (sparse annotations on the dense token sequence), and the
terminal event tag. Aggregate-certainty caching and Window as a first-class
object are downstream concerns and not yet captured here.

Per-step thin records carry the chosen token (id and decoded), its
log-probability, the distribution entropy, the most-probable non-chosen
alternative (id, decoded, probability), and the rank-1/rank-2 logit gap.

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

Terminal event position is implicit as len(steps) — the predicate that
fires terminates after the corresponding step has been appended, so the
last appended step is the terminal step.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StepRecord:
    token_id: int
    token: str
    log_prob: float
    entropy: float
    alt_token_id: int
    alt_token: str
    alt_prob: float
    logit_gap: float


@dataclass(frozen=True)
class StackIdentity:
    """Producing-system identity, captured at trajectory generation time.

    `model_revision` is None when the script does not pin one (i.e., the
    HF default revision was loaded). `deterministic_flags` is a free-form
    dict so the captured set can grow without breaking old packets.
    """
    model_id: str | None
    model_revision: str | None
    dtype: str
    device: str
    torch_version: str
    transformers_version: str
    deterministic_flags: dict[str, Any]


@dataclass(frozen=True)
class PredicateSpec:
    """Name + params for a terminal predicate, captured for reproducibility.

    Built by introspecting the .name and .params attributes attached to
    predicate factories' returned callables.
    """
    name: str
    params: dict[str, Any]


@dataclass(frozen=True)
class InferenceStrategy:
    """The inference plan: name plus any plan-level params.

    Currently always `name="hard_cap_t0"`. Future variants — sliding window,
    temperature sampling, etc. — populate params accordingly. Per-step
    placement events (first_step_override at T=0, sampling deviations at
    T>0) are recorded in the rank-event log, not here.
    """
    name: str
    params: dict[str, Any]


@dataclass(frozen=True)
class RankEvent:
    """Sparse annotation: a step where the chosen token was placed by
    injection or sampled non-rank-0, rather than taken as natural argmax.

    Always logged for injections regardless of whether the placed token
    coincides with the natural argmax — the *fact* of the placement is
    part of the trajectory's provenance. Readers wanting outcome-divergent
    events only filter on chosen_id != natural_argmax_id.
    """
    position: int
    kind: str  # "injection" or "sample"
    chosen_id: int
    natural_argmax_id: int


@dataclass
class Trajectory:
    stack: StackIdentity
    initial_ids: list[int]
    predicates: tuple[PredicateSpec, ...]
    inference_strategy: InferenceStrategy
    steps: list[StepRecord]
    rank_events: list[RankEvent] = field(default_factory=list)
    terminal_event: str = ""

    @property
    def token_ids(self) -> list[int]:
        return [*self.initial_ids, *(s.token_id for s in self.steps)]

    @property
    def length(self) -> int:
        return len(self.steps)
