# Peirce — Basins Catalog

*Append-only catalog of basins identified under hard-cap T=0 inference. Each entry is pinned to the commit and run that produced its initial detection. Basin identity is the cycle token-id tuple — observed in different runs, the same cycle is the same basin. Cycle text is the human-readable decoded form; late-window certainty stats are the adjudication signal.*

*Status: v0.2, refreshed under runtime basin-capture predicate (commit `08b0ba5`). Basin entries are append-only across runs by cycle-token-id identity; the document is reorganized on methodology changes.*

*Basin classification (e.g. local-success-trap vs crystal) is deferred — see [ideas.md](ideas.md) "EOS as implicit-success signal", subsection "local-success traps". Adjudication requires perturbation response, which is not yet implemented.*

---

## Overview as of commit `08b0ba5`

- 19 distinct basins identified across the broad-shallow ensemble (top-100 from `[BOS]`, 64-token budget, hard-cap T=0).
- 28 / 100 trajectories captured by the runtime predicate within budget; 72 / 100 still transient at budget.
- Predicate confirms a tail cycle at K = 4 consecutive repetitions before terminating (see [observations.md](observations.md) `08b0ba5` entry for the methodological rationale and contrast with the v0.1 catalog).
- Captured-trajectory length: mean 20, median 13, range 4–61. The runtime predicate frees ~44 tokens of inference budget per captured trajectory on average vs running to the budget cap.
- 4 basins exhibit coalescence (multiple trajectories landing in the same basin):
  - basin-001 (period-1 single space): 5 trajectories.
  - basin-002 (period-2 double-space-pipe): 4 trajectories.
  - basin-003 (period-3 checkbox): 2 trajectories.
  - basin-004 (period-1 hash-fill): 2 trajectories.
- Late-window mean entropy across basins ranges from 0.64 (very tight, basin-018 phrase) to 4.88 (loose, basin-011 tab-dash). Late-window mean logit-gap ranges from 1.00 (basin-004 hash-fill) to 6.64 (basin-018 phrase).

## Basins

### basin-001 — period 1, single-space repetition
- **Cycle:** `' '` (single space)
- **Trajectories (broad-shallow `08b0ba5`):** 6, 27, 41, 64, 95
- **Late-window stats (representative):** H=2.26, gap=2.98
- **Notes:** Strongest basin coalescence in the ensemble. Whitespace-prefix starts (11–24 spaces) plus the multilingual `[@` start all converge.

### basin-002 — period 2, double-space-pipe table fence
- **Cycle:** `'  |'`
- **Trajectories:** 14, 19, 25, 62
- **Late-window stats:** H=4.45, gap=1.85
- **Notes:** Markdown table fence pattern. Four whitespace-prefix starts converge.

### basin-003 — period 3, checkbox pattern
- **Cycle:** `' [x]'` (and rotations)
- **Trajectories:** 10, 36
- **Late-window stats:** H=4.03, gap=2.52
- **Notes:** Markdown task-list checkbox cycle. Both starts (`'  '` and `' '`) settle in identical cycle alignment under the runtime predicate.

### basin-004 — period 1, hash-fill
- **Cycle:** `'#'` (one `#` per token, repeated)
- **Trajectories:** 49, 92
- **Late-window stats:** H=3.99, gap=1.00
- **Notes:** Code-comment-fence or markdown horizontal-rule basin. Loose gap for a period-1 basin — content varies pre-cycle.

### basin-005 — period 4, table fence with backticks
- **Cycle:** `' `--` |'`
- **Trajectories:** 4
- **Late-window stats:** H=3.81, gap=2.38

### basin-006 — period 5, URL-encoded fragment
- **Cycle:** `'%22%22+'` (and rotations)
- **Trajectories:** 5
- **Late-window stats:** H=2.63, gap=2.07
- **Notes:** Reached after a Google-search URL transient.

### basin-007 — period 3, indented backtick-dash
- **Cycle:** `'-   `'` (and rotations)
- **Trajectories:** 7
- **Late-window stats:** H=4.55, gap=1.58

### basin-008 — period 9, "first thing to note" phrase cycle
- **Cycle:** `' thing to note is that the _first_'` (and rotations of `' the _first_ thing to note is that'`)
- **Trajectories:** 28
- **Late-window stats:** H=2.43, gap=2.84
- **Notes:** Phrase-level basin. The "_first_" subpattern is exactly the kind of opening-token feedback loop discussed in [ideas.md](ideas.md) "EOS-as-success-signal" → "local-success traps": "first" produces continuation, continuation contains another opening, opening invites another "first."

### basin-009 — period 3, newline-plus
- **Cycle:** `'\n\n+'`
- **Trajectories:** 34
- **Late-window stats:** H=3.43, gap=3.46

### basin-010 — period 1, thin-space
- **Cycle:** `' '`
- **Trajectories:** 47
- **Late-window stats:** H=4.46, gap=1.63

### basin-011 — period 2, tab-dash
- **Cycle:** `'\t-'`
- **Trajectories:** 48
- **Late-window stats:** H=4.88, gap=1.69
- **Notes:** Loosest entropy in the catalog.

### basin-012 — period 5, role-path
- **Cycle:** `'/1/roles'` (and rotations)
- **Trajectories:** 50
- **Late-window stats:** H=2.42, gap=2.40
- **Notes:** Likely content-cycle (URL pattern).

### basin-013 — period 2, dash-fill-plus
- **Cycle:** `'+---------------------'`
- **Trajectories:** 57
- **Late-window stats:** H=2.96, gap=2.30

### basin-014 — period 2, longer dash-fill-plus
- **Cycle:** `'+-----------------------------------'`
- **Trajectories:** 63
- **Late-window stats:** H=3.03, gap=2.63
- **Notes:** Distinct cycle token-ids from basin-013 despite visual similarity.

### basin-015 — period 4, code-fence cycle
- **Cycle:** `'\n\n```'`
- **Trajectories:** 65
- **Late-window stats:** H=2.99, gap=3.15
- **Notes:** Markdown code fence opener-closer cycle.

### basin-016 — period 6, table-cell-bold-stat
- **Cycle:** `'   **0.01**'`
- **Trajectories:** 70
- **Late-window stats:** H=1.44, gap=4.49
- **Notes:** Academic-paper table column repetition.

### basin-017 — period 3, replacement-character pattern
- **Cycle:** `' ●'` (token-level: space + replacement-char glyph)
- **Trajectories:** 77
- **Late-window stats:** H=1.79, gap=3.22

### basin-018 — period 15, "list of all the files" phrase cycle
- **Cycle:** `'\n\nThe following is a list of all the files in the project.'`
- **Trajectories:** 81
- **Late-window stats:** H=0.64, gap=6.64
- **Notes:** Tightest basin in the catalog. Phrase-level, sentence-period structure.

### basin-019 — period 10, "data is released" phrase cycle
- **Cycle:** `'\n\nThe data is released to the public.'`
- **Trajectories:** 93
- **Late-window stats:** H=1.75, gap=4.37
- **Notes:** Phrase-level, self-contained sentence-period cycle.

## Notes across the catalog

- **Phrase basins are reproducible at small budget.** basin-008, basin-018, basin-019 reach phrase-level cycles within 64 tokens. Tightness (gap > 4, H < 2) separates these from the structural / fence basins.
- **Basin coalescence is real, concentrated in simple structural basins.** Three of the four coalescing basins are period ≤ 3 single-character or table-fence cycles. The single-space basin absorbs five distinct prefixes; the table-fence basin absorbs four.
- **Tightness varies.** Late-window logit gap ranges from 1.00 (basin-004 hash-fill) to 6.64 (basin-018 phrase). The looser basins (gap < 2, H > 4) are candidates for extended-transient classification rather than true asymptotic basins; depth extension would adjudicate.
- **The 72 / 100 unflagged trajectories** are the open question for the selection-bias probe — do they reach basins by L_arch under the same predicate?

## Catalog history

- **v0.1** (commit `ae95f32`, 24 basins / 32 trajectories): post-hoc detection at depth 64 with K=2 confirmation. Detection reported `repetitions_in_cycle_window` as `tail_n // period` (the trivial maximum), not actual consecutive cycle blocks. Five v0.1 entries were not re-confirmed under v0.2 methodology — `-trump` (period-3, traj 15), Japanese phrase (period-13, traj 37), `\n` (period-1, traj 40), status-table-row (period-14, traj 45), and `I had been up` prose-cycle (period-14, traj 3). All were borderline at K=2 and several were explicitly flagged "possibly extended transient" in the v0.1 entries. They are candidates for adjudication when the selection-bias probe extends non-cycling trajectories to L_arch under the v0.2 predicate.
- **v0.2** (commit `08b0ba5`, this catalog): runtime basin-capture predicate at K=4 confirmation; `repetitions_in_cycle_window` corrected to count actual consecutive cycle blocks back from the tail.

---

*Catalog format and basin-id assignment are provisional. Stable basin identity across runs is the cycle-token-id tuple, not the assigned id; assigned ids are for in-document reference only.*
