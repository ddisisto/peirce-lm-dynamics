# Peirce — Basins Catalog

*Append-only catalog of basins identified under hard-cap T=0 inference. Each entry is pinned to the commit and run that produced its initial detection. Basin identity is the cycle token-id tuple — observed in different runs, the same cycle is the same basin. Cycle text is the human-readable decoded form; late-window certainty stats are the adjudication signal.*

*Status: v0.1, seeded from broad-shallow run on commit `ae95f32`. Format is provisional and will iterate as more specimens land. The catalog is markdown-only for now per the project's "build empirical intuition before designing for scale" stance.*

*Basin classification (e.g. local-success-trap vs crystal) is deferred — see [ideas.md](ideas.md) "EOS as implicit-success signal", subsection "local-success traps". Adjudication requires perturbation response, which is not yet implemented.*

---

## Overview as of commit `ae95f32`

- 24 distinct basins identified across the broad-shallow ensemble (top-100 from `[BOS]`, 64-token budget, hard-cap T=0).
- 32 / 100 trajectories landed in basins within budget; 68 / 100 still transient at budget.
- 3 basins exhibit coalescence (multiple trajectories landing in the same basin):
  - basin-001 (period-1 single space): 5 trajectories.
  - basin-002 (period-2 double-space-pipe): 4 trajectories.
  - basin-003 (period-1 hash-fill): 2 trajectories.
- Late-window mean entropy across basins ranges from 0.15 (very tight) to 2.63 (loose). Late-window mean logit-gap from 1.37 (loose) to 8.69 (very tight). The two metrics broadly co-vary as expected.

## Basins

### basin-001 — period 1, single-space repetition
- **Cycle:** `' '` (single space)
- **Trajectories (broad-shallow `ae95f32`):** 6, 27, 41, 64, 95
- **Late-window stats:** H=1.93, gap=2.54 (loose for a period-1 basin — content varies across the constituent trajectories)
- **Notes:** Strongest basin coalescence in the ensemble. Whitespace-rank starts (11 spaces, 17 spaces, 24 spaces) and a non-whitespace start (`' �'`, rank 95) all converge.

### basin-002 — period 2, double-space-pipe table fence
- **Cycle:** `'  |'`
- **Trajectories:** 14, 19, 25, 62
- **Late-window stats:** H=0.37, gap=5.28
- **Notes:** Markdown table fence pattern. Four whitespace-prefix starts converge.

### basin-003 — period 1, hash-fill
- **Cycle:** `'################################'` (one `#` per token, repeated)
- **Trajectories:** 49, 92
- **Late-window stats:** H=0.33, gap=5.60
- **Notes:** Code-comment-fence or markdown horizontal-rule basin. Tighter than basin-001 despite same period.

### basin-004 — period 4, table fence with backticks
- **Cycle:** `' `--` |'`
- **Trajectories:** 4
- **Late-window stats:** H=0.21, gap=5.28

### basin-005 — period 5, URL-encoded fragment
- **Cycle:** `'22%22+%'`
- **Trajectories:** 5
- **Late-window stats:** H=0.98, gap=3.64

### basin-006 — period 3, indented backtick-dash
- **Cycle:** `'   `-'`
- **Trajectories:** 7
- **Late-window stats:** H=0.15, gap=5.82

### basin-007 — period 3, checkbox-pattern
- **Cycle:** `' [x]'`
- **Trajectories:** 10
- **Late-window stats:** H=0.18, gap=6.29

### basin-008 — period 3, hyphen-trump
- **Cycle:** `'-trump'`
- **Trajectories:** 15
- **Late-window stats:** H=0.95, gap=8.14
- **Notes:** Loosest entropy of the period-3 basins observed; gap is the highest in this family. Possibly content-driven repetition rather than structural fence.

### basin-009 — period 9, "first thing to note" phrase cycle
- **Cycle:** `' the _first_ thing to note is that'`
- **Trajectories:** 28
- **Late-window stats:** H=0.50, gap=4.68
- **Notes:** Phrase-level basin. The "_first_" subpattern is exactly the kind of opening-token feedback loop discussed in ideas.md (EOS-as-success-signal entry, local-success-traps subsection): "first" produces continuation, continuation contains another opening, opening invites another "first."

### basin-010 — period 3, newline-plus
- **Cycle:** `'\n\n+'`
- **Trajectories:** 34
- **Late-window stats:** H=0.15, gap=8.69
- **Notes:** Highest late-window logit-gap in the ensemble.

### basin-011 — period 3, checkbox-bracket
- **Cycle:** `'x] ['`
- **Trajectories:** 36
- **Late-window stats:** H=0.15, gap=6.03

### basin-012 — period 13, Japanese phrase fragment
- **Cycle:** `'することを、自分の生活を支��'` (decode boundary issue at end)
- **Trajectories:** 37
- **Late-window stats:** H=1.82, gap=3.83
- **Notes:** Multilingual basin. Entropy elevated — possibly extended transient rather than true asymptotic basin; needs depth extension to adjudicate.

### basin-013 — period 1, escaped-newline
- **Cycle:** `'\n'`
- **Trajectories:** 40
- **Late-window stats:** H=1.35, gap=3.28
- **Notes:** Distinct from basin-001 (single space) — different cycle token.

### basin-014 — period 14, status-table-row
- **Cycle:** `'\n| **Status**                                                   |\n+---------------------------------------------------------------+'`
- **Trajectories:** 45
- **Late-window stats:** H=0.92, gap=4.99
- **Notes:** Long structural-table cycle.

### basin-015 — period 2, tab-dash
- **Cycle:** `'\t-'`
- **Trajectories:** 48
- **Late-window stats:** H=0.27, gap=4.46

### basin-016 — period 5, role-path
- **Cycle:** `'/roles/1'`
- **Trajectories:** 50
- **Late-window stats:** H=1.64, gap=3.09
- **Notes:** Looks like content-cycle (URL pattern). Higher entropy.

### basin-017 — period 2, dash-fill-plus
- **Cycle:** `'---------------------+'`
- **Trajectories:** 57
- **Late-window stats:** H=0.24, gap=4.48

### basin-018 — period 2, longer dash-fill-plus
- **Cycle:** `'-----------------------------------+'`
- **Trajectories:** 63
- **Late-window stats:** H=0.45, gap=3.49
- **Notes:** Distinct cycle token-ids from basin-017 despite visual similarity.

### basin-019 — period 4, code-fence-cycle
- **Cycle:** `'``\n\n`'`
- **Trajectories:** 65
- **Late-window stats:** H=0.27, gap=5.96
- **Notes:** Markdown code fence opener-closer cycle.

### basin-020 — period 6, table-cell-bold-stat
- **Cycle:** `'**0.01**   '`
- **Trajectories:** 70
- **Late-window stats:** H=0.37, gap=4.40
- **Notes:** Academic-paper table column repetition.

### basin-021 — period 3, replacement-character pattern
- **Cycle:** `'�� �'`
- **Trajectories:** 77
- **Late-window stats:** H=0.19, gap=6.24

### basin-022 — period 15, "list of all the files" phrase cycle
- **Cycle:** `' following is a list of all the files in the project.\n\nThe'`
- **Trajectories:** 81
- **Late-window stats:** H=0.58, gap=6.83
- **Notes:** Phrase-level basin, longer cycle than basin-009.

### basin-023 — period 10, "data is released" phrase cycle
- **Cycle:** `'\nThe data is released to the public.\n'`
- **Trajectories:** 93
- **Late-window stats:** H=0.30, gap=6.90
- **Notes:** Phrase-level basin. Self-contained sentence-period cycle.

### basin-024 — period 14, "I had been up" phrase cycle
- **Cycle:** `' I had been up for almost two hours and I was still awake.'`
- **Trajectories:** 3
- **Late-window stats:** H=2.63, gap=1.37
- **Notes:** Loosest basin observed (highest H, lowest gap). Possibly an extended transient rather than a true asymptotic basin; needs depth extension to adjudicate. Of all 24 basins, this is the most natural-prose specimen.

## Notes across the catalog

- **Phrase basins are present at small budget.** basin-009, -022, -023, -024 reach phrase-level cycles within 64 tokens. These are qualitatively different from the structural / single-character basins (-001, -003, -013) and the table-fence basins (-002, -004, -017, -018, -019, -020).
- **Basin coalescence is real.** Three basins received multiple trajectories from distinct BOS starts. The single-space basin (-001) absorbs five distinct prefixes; the double-space-pipe basin (-002) absorbs four. Whitespace-prefix starts dominate the coalescing basins.
- **Tightness varies.** Late-window logit gap ranges from 1.37 (basin-024, prose-cycle) to 8.69 (basin-010, newline-plus). The looser basins (gap < 3, H > 1.5) are candidates for extended-transient classification rather than true asymptotic basins; depth extension would adjudicate.
- **The 68 / 100 unflagged trajectories** remain the open question for the selection-bias probe — do they reach basins by L_arch under the same probe?

---

*Catalog format and basin-id assignment are provisional. Stable basin identity across runs is the cycle-token-id tuple, not the assigned id; assigned ids are for in-document reference only.*
