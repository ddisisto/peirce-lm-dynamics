"""Predicate framework for terminal-event detection.

A predicate is a callable (history, records, n_steps) -> tag | None, where
history is the running list of token ids (initial + appended), records is
the list of per-step thin records appended so far, and n_steps is its
length. The first predicate to return a non-None tag terminates the
trajectory; the tag becomes the trajectory's terminal_event.

Predicates that need only token-ids (eos, budget_cap, window_cap) ignore
the records argument. Predicates that need probability dynamics (e.g.
basin_capture_predicate, defined alongside detect_tail_cycle in basins.py)
read records.
"""
from __future__ import annotations

from typing import Callable

from .records import StepRecord

Predicate = Callable[[list[int], list[StepRecord], int], str | None]


def eos_predicate(eos_id: int) -> Predicate:
    def check(history: list[int], records: list[StepRecord], n_steps: int) -> str | None:
        return "eos" if history and history[-1] == eos_id else None
    return check


def budget_cap_predicate(budget: int) -> Predicate:
    def check(history: list[int], records: list[StepRecord], n_steps: int) -> str | None:
        return "budget_cap" if n_steps >= budget else None
    return check


def window_cap_predicate(L_arch: int) -> Predicate:
    def check(history: list[int], records: list[StepRecord], n_steps: int) -> str | None:
        return "window_cap" if len(history) >= L_arch else None
    return check
