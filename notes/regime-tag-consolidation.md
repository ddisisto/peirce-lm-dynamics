# Regime-tag consolidation — working plan

*Transitional planning doc. Lives in `notes/` so it stays out of CLAUDE.md's @-included context. Delete once the resolver module + tests have landed and consumers are migrated; the durable form of this content is the module docstring + the tests + the eventual observation entry that pins the consolidation.*

*Provenance: surfaced after the N2 first-batch plot pass when `first_batch_branches.BATCH`'s hand-curated regime-tag column was identified as the load-bearing weak point for further classifier work. Tag-derivation should be a function from substrate primitives, not a manifest.*

---

## Why this exists

The regime tags currently in circulation (`SLOTTED-CLASS`, `SLOTTED-COUNTER-INT/LETTER`, `SLOTTED-MIXED`, `SLOTTED-HARMONIC`, `SCAFFOLD`, `NOPERIOD`, `NOPERIOD-A/B`) wear the same hat but come from three different layers:

- **Catalog-emitted, already operational.** `SLOTTED-CLASS / -COUNTER-INT / -COUNTER-LETTER / -MIXED`, `SCAFFOLD`, `NOPERIOD` — `scripts/shape_catalog.py` derives all of these from period detection over `peaks` + delta-evidence per slot. These are solid.
- **Audit-emitted, operational but script-local.** `NOPERIOD-A` (monotonic acf decay) and `NOPERIOD-B` (bimodal H with weak quasi-periodic peaks under relaxed `PEAK_MIN`) come from `scripts/noperiod_audit.py`. The definition exists; it's just not in the catalog's emitted surface.
- **Observational shorthand, not yet operational.** `SLOTTED-HARMONIC` is from the N1 period-detection-harmonics paragraph in `observations.md`. Implied definition ("strongest peaks form a harmonic ladder at multiples of the fundamental") but no code that emits it.

The pragmatist guard from `foundation.md`: a distinction earns its keep by predicting on un-narrated specimens. SLOTTED-HARMONIC currently doesn't have a predicate — it has a story. NOPERIOD-A/B has a predicate but in the wrong place.

## Sequence

### 1. Audit pass (script)

`scripts/regime_tag_audit.py` — read-only over the store; no model load.

For every trajectory:
- catalog-emitted tag (from `shape_catalog`-style logic)
- NOPERIOD-A/B classification (from `noperiod_audit`-style logic, where applicable)
- candidate SLOTTED-HARMONIC classification (a first-draft predicate over `peaks`)
- manifest tag from `first_batch_branches.BATCH` (where present)
- raw shape primitives (`peaks`, `floor_H`, `osc_amp`)

Surfaces:
- divergences between catalog/audit/candidate vs manifest — places where the human eye saw something the code didn't, or vice versa
- coverage gaps — manifest tags with no operational equivalent
- cross-tag overlaps — specimens satisfying multiple sub-tag definitions, which directly informs the multi-tag question below

Output is a stdout table; no figures. The audit is the *test* for the resolver design — what the audit shows determines the API choices that follow.

### 2. Resolver module

`peirce/regime.py` (new module). Sibling to `peirce/shape.py`, depends on it.

Initial API (first cut, flat-string):

```python
def regime_tag(steps: list[StepRecord], deep_start: int = DEEP_START) -> str:
    """Single canonical regime tag derived from substrate primitives.
    
    Returns one of: "SLOTTED-CLASS" | "SLOTTED-COUNTER-INT" | ...
                    | "SCAFFOLD" | "NOPERIOD-A" | "NOPERIOD-B"
    """
```

Stays in a separate module rather than living in `peirce/shape.py` because regime-tag is a *taxonomic* concept layered on shape primitives; keeping shape.py focused on raw measurements makes both layers easier to reason about.

If the audit shows specimens satisfying multiple sub-tag definitions cleanly (e.g., a trajectory that's both SLOTTED-CLASS and SLOTTED-HARMONIC because the two axes — slot content and peak structure — are orthogonal), promote to a structured return:

```python
@dataclass(frozen=True)
class RegimeTag:
    umbrella: str                    # "SLOTTED" | "SCAFFOLD" | "NOPERIOD"
    slot_character: str | None       # "CLASS" | "COUNTER-INT" | ...
    peak_structure: str | None       # "HARMONIC" | "SINGLE" | "SUB-PERIODIC"
    noperiod_cluster: str | None     # "A" | "B"
```

Decide between flat-string and structured *after* the audit pass — both options are real, and forcing the decision before the data exists is the kind of over-design the discipline guards against.

### 3. Operationalise definitions

Three things need pinning before the resolver can emit them:

**SLOTTED-HARMONIC.** Candidate predicate, refined against the audit:

> `len(peaks) >= 3` and `peaks[1].lag` and `peaks[2].lag` are integer multiples of `peaks[0].lag` within tolerance ±1 step. Equivalently: the autocorrelation shows a clean harmonic ladder rooted at the fundamental.

Tolerance, minimum-peak-count, and whether to include `peaks[0]` itself in the ladder check all want grounding against the 7 manifest specimens + whatever else the predicate catches. The N1 observation entry's language is the reference; the implementation tightens it.

**NOPERIOD-A vs NOPERIOD-B.** Lift from `noperiod_audit.py`:

- **A** — monotonic acf decay; no strict-local-max peaks under relaxed `PEAK_MIN` either.
- **B** — bimodal H *and* weak quasi-periodic peaks under relaxed `PEAK_MIN` (peaks exist that don't pass the catalog's default threshold).

The audit's existing relaxed-`PEAK_MIN` + widened-`LAG_MAX` parameters become module constants in `peirce/regime.py`. The "bimodal H" criterion needs operational form — first cut: H histogram has two distinguishable modes by, e.g., a simple bimodality coefficient or two-cluster fit. Audit pass tells us how robust this is at n=8.

**SLOTTED-MIXED** is already catalog-emitted but worth re-checking against the audit — its precedence relative to COUNTER and CLASS sub-tags is currently implicit.

### 4. Refactor consumers

Once the resolver is in place:

- `scripts/shape_catalog.py` — emit `regime_tag(steps)` as the canonical tag column; the catalog's existing per-tag-grouped sections still drive their groupings off the same function. Net effect: less inline tag-classification logic in the script.
- `scripts/first_batch_branches.py` — `BATCH` column drops the regime-tag entries; becomes a list of prefixes. Tag is read back via `regime_tag(parent.steps)` at log time. The hand-curated list becomes an audit ground-truth set, not the source of truth.
- `scripts/branch_compare.py` — emits parent regime-tag + branch regime-tag per pair. Regime-transition becomes a sharper basin-switch signal than the current peak-acf-delta heuristic. Heuristic classifier stays (it's still useful for the wandering/re-absorbed distinction *within* a held-constant regime) but gets a "regime-tag changed" column alongside.
- `scripts/plot_branches.py` — drop the `first_batch_branches.BATCH` import; call `regime_tag(parent.steps)` for grids-by-regime.
- `scripts/noperiod_audit.py` — keeps its parameter-sweep diagnostic role, but the A/B classification it currently emits gets lifted into `peirce/regime.py`. The audit script becomes a tuning-time tool, not a runtime classifier.

### 5. Tests

Minimal pytest suite for `peirce/regime.py`. For each of the seven tags, at least one specimen from the substrate (pinned by trajectory_id prefix in the test) with the expected resolver output. Edge cases: very short trajectory (deep window doesn't exist), borderline NOPERIOD specimens, COUNTER-vs-CLASS borderline.

Tests double as definition-by-example for the tags. If a future re-audit forces a definition change, the tests are where the change is registered.

## Open questions / parked

- **Single-tag vs structured tag.** Audit pass decides. If specimens cleanly inhabit one regime per axis, flat-string is enough; if axes are genuinely orthogonal at substrate scale, structured.
- **Per-trajectory persistence.** Not for first pass. Resolver is a pure function over the per-step records already in the store; computing on read costs ~ms per trajectory. Persisting the tag as a column would denormalise. Re-examine if a downstream consumer needs cross-trajectory queries that the pure-function approach can't satisfy in tolerable time.
- **Cycle 3 inheritance.** Per `design-reqs.md`'s cycle-to-cycle inheritance discipline, the resolver should be foundation-stable: tags are functions of per-step records, not of cycle-2-vintage classifications. Definitions revisable; the *function-from-substrate* commitment is durable.
- **Cross-checking against the heuristic outcome classifier.** Once regime-tag is canonical, `branch_compare.py`'s {re-absorbed, wandering, basin-switch} classifier can be re-evaluated against {regime preserved, regime changed} as a coarser axis. May surface that the heuristic captures something the regime-tag transition doesn't, or vice versa.

## Forward-sequence slot (for next CLAUDE.md pass)

This work belongs in the forward sequence as a new substrate-consolidation move, inserted between current move 3 (matplotlib companion — done) and current move 4 (completion-space enumeration). Proposed new ordering:

- 3 — matplotlib companion to `branch_compare.py` *(done)*
- **4 — regime-tag consolidation (this doc's plan)**
- 5 — completion-space enumeration at low T *(was 4)*
- 6 — transient-window perturbation batch *(was 5)*
- 7 — burn-in threshold revision for `DEEP_START` *(was 6)*

Both move 6 (transient window) and move 7 (burn-in revision) benefit directly from the canonical regime-tag surface this consolidation lands; move 5 (completion-space) benefits because "what regimes are reachable from this position at temperature T" becomes a clean readout once tag-derivation is automatic.

CLAUDE.md revision lands as the first move of the next code pass, alongside the audit script.
