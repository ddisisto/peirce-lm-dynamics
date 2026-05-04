"""SQLite-backed trajectory and observation store.

Schema reflects the trajectory-vs-observation split from records.py:

- `trajectories` — one row per underlying trajectory, keyed by
  trajectory_id (hash of stack + initial_ids + injections).
- `trajectory_steps` — per-step thin records, FK to trajectory.
- `observations` — one row per experimenter's run, keyed by
  observation_id (hash of trajectory_id + predicates + inference_strategy),
  carrying terminal_event and observed_length.

A trajectory's steps are stored once. Multiple observations of the same
trajectory at different depths share storage. An observation's "steps"
view is `trajectory_steps[:observed_length]`.

Write semantics are write-once on observation_id: a re-run of the same
manifest is a no-op. Trajectory rows are upserted (existing trajectory
keeps its row; new steps appended for positions not already stored).
Cross-stack re-runs for validation are a separate code path that
compares step-by-step without writing.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterator

from .records import (
    InferenceStrategy,
    Injection,
    Observation,
    PredicateSpec,
    StackIdentity,
    StepRecord,
    Trajectory,
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS trajectories (
    trajectory_id TEXT PRIMARY KEY,
    model_id TEXT,
    model_revision TEXT,
    dtype TEXT NOT NULL,
    device TEXT NOT NULL,
    torch_version TEXT NOT NULL,
    transformers_version TEXT NOT NULL,
    deterministic_flags_json TEXT NOT NULL,
    initial_ids_json TEXT NOT NULL,
    injections_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS trajectory_steps (
    trajectory_id TEXT NOT NULL REFERENCES trajectories(trajectory_id),
    position INTEGER NOT NULL,
    token_id INTEGER NOT NULL,
    token TEXT NOT NULL,
    log_prob REAL NOT NULL,
    entropy REAL NOT NULL,
    alt_token_id INTEGER NOT NULL,
    alt_token TEXT NOT NULL,
    alt_prob REAL NOT NULL,
    logit_gap REAL NOT NULL,
    PRIMARY KEY (trajectory_id, position)
);

CREATE TABLE IF NOT EXISTS observations (
    observation_id TEXT PRIMARY KEY,
    trajectory_id TEXT NOT NULL REFERENCES trajectories(trajectory_id),
    predicates_json TEXT NOT NULL,
    inference_strategy_name TEXT NOT NULL,
    inference_strategy_params_json TEXT NOT NULL,
    terminal_event TEXT NOT NULL,
    observed_length INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_trajectories_model ON trajectories(model_id);
CREATE INDEX IF NOT EXISTS idx_observations_trajectory ON observations(trajectory_id);
CREATE INDEX IF NOT EXISTS idx_observations_terminal ON observations(terminal_event);
"""


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _stack_dict(stack: StackIdentity) -> dict[str, Any]:
    return {
        "model_id": stack.model_id,
        "model_revision": stack.model_revision,
        "dtype": stack.dtype,
        "device": stack.device,
        "torch_version": stack.torch_version,
        "transformers_version": stack.transformers_version,
        "deterministic_flags": stack.deterministic_flags,
    }


def _injections_list(injections: tuple[Injection, ...]) -> list[dict[str, Any]]:
    return [{"position": i.position, "chosen_id": i.chosen_id} for i in injections]


def _predicates_list(predicates: tuple[PredicateSpec, ...]) -> list[dict[str, Any]]:
    return [{"name": p.name, "params": p.params} for p in predicates]


def trajectory_hash_from_parts(
    stack: StackIdentity,
    initial_ids: list[int],
    injections: tuple[Injection, ...],
) -> str:
    """Deterministic id from trajectory identity fields."""
    manifest = {
        "stack": _stack_dict(stack),
        "initial_ids": list(initial_ids),
        "injections": _injections_list(injections),
    }
    payload = _canonical_json(manifest).encode("utf-8")
    return hashlib.blake2b(payload, digest_size=16).hexdigest()


def trajectory_hash(traj: Trajectory) -> str:
    return trajectory_hash_from_parts(traj.stack, traj.initial_ids, traj.injections)


def observation_hash_from_parts(
    trajectory_id: str,
    predicates: tuple[PredicateSpec, ...],
    inference_strategy: InferenceStrategy,
) -> str:
    """Deterministic id from observation identity fields."""
    manifest = {
        "trajectory_id": trajectory_id,
        "predicates": _predicates_list(predicates),
        "inference_strategy": {
            "name": inference_strategy.name,
            "params": inference_strategy.params,
        },
    }
    payload = _canonical_json(manifest).encode("utf-8")
    return hashlib.blake2b(payload, digest_size=16).hexdigest()


def observation_hash(obs: Observation) -> str:
    return observation_hash_from_parts(
        trajectory_hash(obs.trajectory),
        obs.predicates,
        obs.inference_strategy,
    )


def open_store(path: str | Path) -> sqlite3.Connection:
    """Open (or create) a packet store at `path`. Initializes schema if new."""
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def _write_trajectory_row_if_new(conn: sqlite3.Connection, traj: Trajectory) -> str:
    """Insert the trajectory row if absent. Returns trajectory_id."""
    tid = trajectory_hash(traj)
    cur = conn.execute("SELECT 1 FROM trajectories WHERE trajectory_id = ?", (tid,))
    if cur.fetchone() is None:
        conn.execute(
            """INSERT INTO trajectories (
                trajectory_id, model_id, model_revision, dtype, device,
                torch_version, transformers_version, deterministic_flags_json,
                initial_ids_json, injections_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                tid,
                traj.stack.model_id,
                traj.stack.model_revision,
                traj.stack.dtype,
                traj.stack.device,
                traj.stack.torch_version,
                traj.stack.transformers_version,
                _canonical_json(traj.stack.deterministic_flags),
                _canonical_json(list(traj.initial_ids)),
                _canonical_json(_injections_list(traj.injections)),
            ),
        )
    return tid


def _append_new_steps(
    conn: sqlite3.Connection, trajectory_id: str, traj: Trajectory
) -> int:
    """Append any trajectory steps not yet stored. Returns count appended."""
    row = conn.execute(
        "SELECT COUNT(*) FROM trajectory_steps WHERE trajectory_id = ?",
        (trajectory_id,),
    ).fetchone()
    n_stored = row[0]
    n_total = len(traj.steps)
    if n_total <= n_stored:
        return 0
    new_rows = [
        (
            trajectory_id, i, s.token_id, s.token, s.log_prob, s.entropy,
            s.alt_token_id, s.alt_token, s.alt_prob, s.logit_gap,
        )
        for i, s in enumerate(traj.steps[n_stored:], start=n_stored)
    ]
    conn.executemany(
        """INSERT INTO trajectory_steps (
            trajectory_id, position, token_id, token, log_prob, entropy,
            alt_token_id, alt_token, alt_prob, logit_gap
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        new_rows,
    )
    return len(new_rows)


def write_observation(conn: sqlite3.Connection, obs: Observation) -> str:
    """Persist an observation. Returns observation_id.

    Writes the trajectory row if new, appends any newly-materialized steps,
    and inserts the observation row (write-once: existing observation_id
    is a no-op).
    """
    tid = _write_trajectory_row_if_new(conn, obs.trajectory)
    _append_new_steps(conn, tid, obs.trajectory)

    oid = observation_hash(obs)
    cur = conn.execute(
        "SELECT 1 FROM observations WHERE observation_id = ?", (oid,)
    )
    if cur.fetchone() is None:
        conn.execute(
            """INSERT INTO observations (
                observation_id, trajectory_id, predicates_json,
                inference_strategy_name, inference_strategy_params_json,
                terminal_event, observed_length
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                oid, tid,
                _canonical_json(_predicates_list(obs.predicates)),
                obs.inference_strategy.name,
                _canonical_json(obs.inference_strategy.params),
                obs.terminal_event,
                obs.observed_length,
            ),
        )
    conn.commit()
    return oid


def _read_trajectory_by_id(
    conn: sqlite3.Connection, trajectory_id: str
) -> Trajectory:
    row = conn.execute(
        """SELECT model_id, model_revision, dtype, device,
                  torch_version, transformers_version, deterministic_flags_json,
                  initial_ids_json, injections_json
           FROM trajectories WHERE trajectory_id = ?""",
        (trajectory_id,),
    ).fetchone()
    if row is None:
        raise KeyError(trajectory_id)

    (model_id, model_revision, dtype, device, torch_version,
     transformers_version, det_flags_json,
     initial_ids_json, injections_json) = row

    stack = StackIdentity(
        model_id=model_id,
        model_revision=model_revision,
        dtype=dtype,
        device=device,
        torch_version=torch_version,
        transformers_version=transformers_version,
        deterministic_flags=json.loads(det_flags_json),
    )
    initial_ids = json.loads(initial_ids_json)
    injections = tuple(
        Injection(position=i["position"], chosen_id=i["chosen_id"])
        for i in json.loads(injections_json)
    )

    step_rows = conn.execute(
        """SELECT token_id, token, log_prob, entropy,
                  alt_token_id, alt_token, alt_prob, logit_gap
           FROM trajectory_steps WHERE trajectory_id = ? ORDER BY position""",
        (trajectory_id,),
    ).fetchall()
    steps = [
        StepRecord(
            token_id=r[0], token=r[1], log_prob=r[2], entropy=r[3],
            alt_token_id=r[4], alt_token=r[5], alt_prob=r[6], logit_gap=r[7],
        )
        for r in step_rows
    ]

    return Trajectory(
        stack=stack,
        initial_ids=initial_ids,
        injections=injections,
        steps=steps,
    )


def read_trajectory(
    conn: sqlite3.Connection, trajectory_id: str
) -> Trajectory:
    """Read a trajectory and all its materialized steps. Raises KeyError if missing."""
    return _read_trajectory_by_id(conn, trajectory_id)


def find_trajectory(
    conn: sqlite3.Connection, traj: Trajectory
) -> Trajectory | None:
    """Look up a trajectory by hash. Returns stored version (with all steps) or None."""
    tid = trajectory_hash(traj)
    cur = conn.execute("SELECT 1 FROM trajectories WHERE trajectory_id = ?", (tid,))
    if cur.fetchone() is None:
        return None
    return _read_trajectory_by_id(conn, tid)


def read_observation(
    conn: sqlite3.Connection, observation_id: str
) -> Observation:
    """Reconstruct an Observation. Raises KeyError if missing."""
    row = conn.execute(
        """SELECT trajectory_id, predicates_json,
                  inference_strategy_name, inference_strategy_params_json,
                  terminal_event, observed_length
           FROM observations WHERE observation_id = ?""",
        (observation_id,),
    ).fetchone()
    if row is None:
        raise KeyError(observation_id)
    (tid, predicates_json, strategy_name, strategy_params_json,
     terminal_event, observed_length) = row

    trajectory = _read_trajectory_by_id(conn, tid)
    predicates = tuple(
        PredicateSpec(name=p["name"], params=p["params"])
        for p in json.loads(predicates_json)
    )
    inference_strategy = InferenceStrategy(
        name=strategy_name,
        params=json.loads(strategy_params_json),
    )
    return Observation(
        trajectory=trajectory,
        predicates=predicates,
        inference_strategy=inference_strategy,
        terminal_event=terminal_event,
        observed_length=observed_length,
    )


def find_observation(
    conn: sqlite3.Connection,
    trajectory_id: str,
    predicates: tuple[PredicateSpec, ...],
    inference_strategy: InferenceStrategy,
) -> Observation | None:
    """Look up an observation by manifest. Returns it or None."""
    oid = observation_hash_from_parts(trajectory_id, predicates, inference_strategy)
    cur = conn.execute("SELECT 1 FROM observations WHERE observation_id = ?", (oid,))
    if cur.fetchone() is None:
        return None
    return read_observation(conn, oid)


def query_observations(
    conn: sqlite3.Connection,
    *,
    trajectory_id: str | None = None,
    terminal_event: str | None = None,
    model_id: str | None = None,
) -> Iterator[str]:
    """Yield observation_ids matching the given filters. Filters compose as AND."""
    clauses: list[str] = []
    params: list[Any] = []
    join = ""
    if trajectory_id is not None:
        clauses.append("o.trajectory_id = ?")
        params.append(trajectory_id)
    if terminal_event is not None:
        clauses.append("o.terminal_event = ?")
        params.append(terminal_event)
    if model_id is not None:
        join = "JOIN trajectories t ON o.trajectory_id = t.trajectory_id"
        clauses.append("t.model_id = ?")
        params.append(model_id)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    cur = conn.execute(
        f"SELECT o.observation_id FROM observations o {join} {where} ORDER BY o.created_at",
        params,
    )
    for (oid,) in cur:
        yield oid
