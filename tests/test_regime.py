"""Pinned-specimen tests for `peirce.regime`.

Definition-by-example: each parametrised row pins a specimen by
`trajectory_id` prefix and the structured tag the resolver should return.
A re-audit that wants to change a definition lands the change here too.

Specimens are drawn from the substrate at `data/peirce.db`; tests skip
when the substrate isn't available, so the test suite is runnable in
contexts without the full store. Where a specimen disagrees with the
manifest in `scripts/first_batch_branches.BATCH`, the audit-finding
reasoning is in the row comment and in `notes/regime-tag-consolidation.md`.

Lifecycle note: this suite is colocated with the resolver, not in
`scripts/`'s smoke-test set. The discipline difference is intentional —
smoke tests are end-to-end checks of runner/store/engine invariants
(usually with their own in-memory store); these are pure-function unit
tests over the persisted substrate. If the two test surfaces want
consolidating later, the merge direction is open.
"""
from __future__ import annotations

import pytest

from peirce.regime import RegimeTag, regime_tag
from peirce.runner import default_store_path
from peirce.store import open_store, read_trajectory


@pytest.fixture(scope="module")
def store():
    path = default_store_path()
    if not path.exists():
        pytest.skip(f"substrate store not found at {path}")
    conn = open_store(path)
    yield conn
    conn.close()


def _read_by_prefix(conn, prefix: str):
    rows = conn.execute(
        "SELECT trajectory_id FROM trajectories WHERE trajectory_id LIKE ?",
        (f"{prefix}%",),
    ).fetchall()
    if len(rows) == 0:
        pytest.skip(f"no trajectory matching prefix {prefix!r} in store")
    if len(rows) > 1:
        pytest.fail(f"prefix {prefix!r} matched {len(rows)} trajectories")
    return read_trajectory(conn, rows[0][0])


SPECIMENS = [
    # (prefix, expected, note)
    ("49ba0b75", RegimeTag(umbrella="SLOTTED", slot_character="CLASS"),
     "textbook class slot; manifest=SLOTTED-CLASS"),
    ("13f9cd8d", RegimeTag(umbrella="SLOTTED", slot_character="COUNTER-INT",
                           peak_structure="HARMONIC"),
     "counter-int slot with harmonic peak ladder; manifest=SLOTTED-COUNTER-INT"),
    ("d2562221", RegimeTag(umbrella="SLOTTED", slot_character="COUNTER-LETTER",
                           peak_structure="HARMONIC"),
     "counter-letter slot with harmonic peak ladder; manifest=SLOTTED-COUNTER-LETTER"),
    ("8ea1fab2", RegimeTag(umbrella="SCAFFOLD", peak_structure="HARMONIC"),
     "scaffold cycle with harmonic peak ladder; manifest=SCAFFOLD"),
    ("edb2b7cf", RegimeTag(umbrella="SCAFFOLD"),
     "scaffold cycle, no harmonic ladder (deep-lag period only); manifest=SCAFFOLD"),
    ("53e800cb", RegimeTag(umbrella="NOPERIOD", noperiod_cluster="A"),
     "honest no-period; manifest=NOPERIOD-A"),
    ("48a13037", RegimeTag(umbrella="NOPERIOD", noperiod_cluster="B"),
     "weak quasi-periodic peaks below default threshold; manifest=NOPERIOD-B"),
    ("7b3233ed", RegimeTag(umbrella="SLOTTED", slot_character="MIXED",
                           peak_structure="HARMONIC"),
     "mixed slot characters across phase positions"),
    # Borderline / audit-divergence specimen — the resolver finds period=2
    # slot content the hand-curated BATCH manifest tagged SCAFFOLD. Pinned
    # here as the canonical SCAFFOLD/SLOTTED edge case; behaviour is the
    # resolver's, not the manifest's.
    ("fa70f050", RegimeTag(umbrella="SLOTTED", slot_character="CLASS",
                           peak_structure="HARMONIC"),
     "audit disagreement: manifest=SCAFFOLD but catalog finds period=2 slot content"),
]


@pytest.mark.parametrize(
    "prefix,expected,note",
    SPECIMENS,
    ids=[s[0] for s in SPECIMENS],
)
def test_regime_tag_specimens(store, prefix, expected, note):
    traj = _read_by_prefix(store, prefix)
    actual = regime_tag(traj.steps)
    assert actual == expected, f"{prefix}: {note}\n  expected {expected}\n  got      {actual}"


def test_flat_string_roundtrip(store):
    """Flat-string property carries the same information at single-axis specimens."""
    traj = _read_by_prefix(store, "49ba0b75")
    tag = regime_tag(traj.steps)
    assert tag.flat == "SLOTTED-CLASS"


def test_flat_string_with_harmonic(store):
    traj = _read_by_prefix(store, "13f9cd8d")
    tag = regime_tag(traj.steps)
    assert tag.flat == "SLOTTED-COUNTER-INT+HARMONIC"


def test_too_short_trajectory_raises(store):
    """`regime_tag` requires `len(steps) > deep_start`."""
    traj = _read_by_prefix(store, "49ba0b75")
    short = traj.steps[:100]
    with pytest.raises(ValueError, match="deep window"):
        regime_tag(short)
