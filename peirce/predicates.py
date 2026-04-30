"""Predicate framework for terminal-event detection.

A predicate is a callable (history, n_steps) -> tag | None, where history is
the running list of token ids (initial + appended) and n_steps is the number
of steps appended so far. The first predicate to return a non-None tag
terminates the trajectory; the tag becomes the trajectory's terminal_event.

Per design-reqs v2.1, the four first-cycle terminal events are intrinsic
(eos, candidate_basin) or extrinsic (budget_cap, window_cap). Candidate-basin
detection is deferred — we don't yet know what signature it should match —
and is added as a fourth predicate once specimens warrant.
"""
from __future__ import annotations

from typing import Callable

Predicate = Callable[[list[int], int], str | None]


def eos_predicate(eos_id: int) -> Predicate:
    def check(history: list[int], n_steps: int) -> str | None:
        return "eos" if history and history[-1] == eos_id else None
    return check


def budget_cap_predicate(budget: int) -> Predicate:
    def check(history: list[int], n_steps: int) -> str | None:
        return "budget_cap" if n_steps >= budget else None
    return check


def window_cap_predicate(L_arch: int) -> Predicate:
    def check(history: list[int], n_steps: int) -> str | None:
        return "window_cap" if len(history) >= L_arch else None
    return check
