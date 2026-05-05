"""Trajectory and Observation dataclasses.

Per design-reqs-records.md plus a refinement that emerged in persistence
design: a *trajectory* is what the model produces under a stack, initial
condition, and any experimenter-specified injections. It unfolds
deterministically under hard-cap T=0 out to the architectural context
length. An *observation* is an experimenter's act of running that
trajectory under a predicate set and stopping when a predicate fires.

Multiple observations can share the same underlying trajectory. A
budget=64 observation and a budget=256 observation of the same trajectory
agree on the first 64 steps; the longer observation extends the
trajectory with the next 192 steps. The store records each trajectory's
materialized steps once, with observation rows referencing the
trajectory by id.

Identity:
- trajectory_id = hash of (stack, initial_ids, injections)
- observation_id = hash of (trajectory_id, predicates, inference_strategy)

Per-step thin records carry the chosen token (id and decoded), its
log-probability, the distribution entropy, the most-probable non-chosen
alternative (id, decoded, probability), and the rank-1/rank-2 logit gap.

The alt fields always identify the dominant alternative to chosen. At T=0
argmax steps the alternative is rank-2 of the distribution and the pair
(log_prob, alt_prob) measures escape pressure. At injection-overridden
or T>0 sampled steps the alternative is rank-1 (the model's argmax
preference) and the pair measures divergence between trajectory and
model intent. At injection points the rank-1 / chosen divergence is
discoverable by joining trajectory.injections with the step at that
position.

The logit_gap is the rank-1 minus rank-2 log-probability (equivalently,
the rank-1 minus rank-2 logit, since softmax shifts both by the same
per-step constant). It is the numerical-noise margin: cross-system
argmax disagreement at this step is plausible when logit_gap falls below
the producing stack's effective floating-point noise floor (typically
~1e-3 to ~1e-4 in fp32, larger in lower precision).
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
class Injection:
    """Experimenter-specified intent to force a token at a specific step.

    Position is 0-indexed within the trajectory's steps (not within the
    full history, which would include initial_ids). An injection at
    position 0 forces the first generated token; position 1 forces the
    second; etc.

    Injections are part of trajectory identity because they shape what
    the model produces. T>0 sample-type non-argmax events (when those
    land) belong to observations rather than trajectories — they are
    outcomes of a stochastic inference run, not intents.
    """
    position: int
    chosen_id: int


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

    Currently always `name="hard_cap_t0"`. Future variants — sliding
    window, temperature sampling, etc. — populate params accordingly.
    Per-step placement events (injections at T=0, sampling deviations
    at T>0) are recorded outside the inference strategy: injections on
    the trajectory, sampling deviations on the observation.
    """
    name: str
    params: dict[str, Any]


@dataclass
class Trajectory:
    """The underlying object: what the model produces under (stack, initial, injections).

    Defined out to L_arch by the model's deterministic unfolding under
    hard-cap T=0 plus any specified injections. The `steps` field holds
    the steps materialized so far across all observations of this
    trajectory. Observations may observe shorter prefixes — see
    Observation.observed_length.

    Mutable: extending a trajectory under a longer-budget observation
    appends to `steps` in place. Identity-defining fields (stack,
    initial_ids, injections) are not modified after construction.
    """
    stack: StackIdentity
    initial_ids: list[int]
    injections: tuple[Injection, ...]
    steps: list[StepRecord] = field(default_factory=list)

    @property
    def materialized_length(self) -> int:
        return len(self.steps)


@dataclass(frozen=True)
class Observation:
    """An experimenter's act of running a trajectory under predicates.

    Identity is (trajectory_id, predicates, inference_strategy). Two
    observations of the same trajectory under the same predicates and
    inference strategy are the same observation. Two observations of
    the same trajectory under different predicates (e.g., budget=64 vs
    budget=256) are distinct observations that share trajectory steps.

    `observed_length` is the position at which a predicate fired,
    terminating this observation. The trajectory itself may have more
    materialized steps if a longer-budget observation has been recorded
    against it.
    """
    trajectory: Trajectory
    predicates: tuple[PredicateSpec, ...]
    inference_strategy: InferenceStrategy
    terminal_event: str
    observed_length: int

    @property
    def steps(self) -> list[StepRecord]:
        return self.trajectory.steps[:self.observed_length]

    @property
    def token_ids(self) -> list[int]:
        return [
            *self.trajectory.initial_ids,
            *(s.token_id for s in self.steps),
        ]

    @property
    def length(self) -> int:
        return self.observed_length
