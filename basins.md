# Peirce — Basins Catalog

*Append-only catalog of basins identified under hard-cap T=0 inference. Each entry is pinned to the commit and run that produced its initial detection. Basin identity is the cycle token-id tuple — observed in different runs, the same cycle is the same basin. Cycle text is the human-readable decoded form; late-window certainty stats are the adjudication signal.*

*Status: v0.3, extended at depth under the selection-bias probe (commit `882ae6d`). Basin entries are append-only across runs by cycle-token-id identity; the document is reorganized on methodology changes.*

*Basin classification (e.g. local-success-trap vs crystal) is deferred — see [ideas.md](ideas.md) "EOS as implicit-success signal", subsection "local-success traps". Adjudication requires perturbation response, which is not yet implemented.*

---

## Overview as of commit `882ae6d`

- 52 distinct basins identified across the selection-bias ensemble (top-100 from `[BOS]`, no budget cap, run to L_arch=2048 under the runtime basin-capture predicate at K=4 with `max_period=32, cycle_window=256, stats_window=256`).
- 61 / 100 trajectories captured (terminal `candidate-basin`); 39 / 100 reached `window_cap` at L_arch and remain transient.
- All 19 v0.2 basins reproduced with identical membership and signatures. 33 new basins surfaced at depth, predominantly long-period (period 11–26) phrase / boilerplate / table-row cycles.
- Four of five v0.1-demoted entries (trajectories 3, 15, 37, 45) re-confirmed as proper basins at depth under K=4 — they were real, just below threshold at the broad-shallow budget. Trajectory 40 captures into a different basin (period-18 phrase) than its v0.1 period-1 newline assignment, which now reads as a misidentification.
- Capture-depth distribution is bimodal: 28 at ≤64 (broad-shallow regime), 28 at 65–256 (modest-extension regime), 5 at 257–1024 (sparse), 0 at 1025–2047. The ~1000-token cutoff is sharp — past that depth, capture does not occur within L_arch.
- 4 basins exhibit coalescence (membership unchanged from v0.2): basin-001 (period-1 single space, 5 traj), basin-002 (period-2 double-space-pipe, 4 traj), basin-003 (period-3 checkbox, 2 traj), basin-004 (period-1 hash-fill, 2 traj). All 33 new basins are singletons within this 100-trajectory ensemble.
- Late-window mean entropy across the catalog now ranges from 0.15 (extremely tight, basin-024 `'.data.cuda'`) to 4.88 (loose, basin-011 tab-dash). Late-window mean logit-gap ranges from ~1.0 (basin-004 hash-fill) to 7.37 (basin-024 `'.data.cuda'`).

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

## Basins surfaced at depth (selection-bias probe `882ae6d`)

*All entries below are singletons within the top-100 ensemble, captured by the runtime predicate when the broad-shallow budget was extended to L_arch=2048. Probe parameters were `max_period=32, cycle_window=256, stats_window=256` (extended from v0.2's `16/64/32` to admit longer-period phrase basins). Predominantly long-period (11–26) phrase / boilerplate / table-row cycles. Capture lengths span 65–844; see [observations.md](observations.md) `882ae6d` entry for the depth distribution and the bimodal-capture finding.*

### basin-020 — period 11, "Chromium browser" authorship phrase
- **Cycle:** `' of the Chromium browser. He is also the author'`
- **Trajectory:** 0 (`'\n'` start, p=0.4402 — the model's argmax of BOS); captured at length 221.
- **Late-window stats:** H=2.05, gap=2.79
- **Notes:** Phrase-level memorized boilerplate from a contributor list. Was first seen at the `343e2fc` representative-deep run on rank-0; held under the runtime predicate at the same cycle alignment.

### basin-021 — period 24, multilingual code-comment instance-create
- **Cycle:** `'\n\n    # 创建一个新的实例\n    self.instance = self.create_instance()'`
- **Trajectory:** 1 (`'\n\n'` start); captured at length 96.
- **Late-window stats:** H=1.36, gap=4.37
- **Notes:** Code-context, Chinese comment then Python self-reference. The training distribution's bilingual code-doc structure surfaces as a phrase basin when given two-newline preamble.

### basin-022 — period 14, "I had been up" prose cycle
- **Cycle:** `'. I had been up for almost two hours and I was still awake'`
- **Trajectory:** 3 (`'*'` start); captured at length 91.
- **Late-window stats:** H=2.66, gap=2.02
- **Notes:** v0.1-demoted entry now confirmed at depth. Loose stats relative to the structural basins; the most natural-prose specimen in the catalog.

### basin-023 — period 3, version-suffix `_v6`
- **Cycle:** `'_v6'` (and rotations)
- **Trajectory:** 9 (`';'` start); captured at length 302.
- **Late-window stats:** H=0.63, gap=4.50
- **Notes:** Version-suffix lock-in inside identifier-naming context.

### basin-024 — period 5, `.data.cuda` attribute chain
- **Cycle:** `'.data.cuda'` (and rotations)
- **Trajectory:** 13 (`'",'` start); captured at length 844 — the deepest capture in the ensemble.
- **Late-window stats:** H=0.15, gap=7.37 — **tightest specimen in the catalog**.
- **Notes:** PyTorch attribute-chain lock-in. Despite the long pre-cycle transient, the eventual basin is essentially deterministic.

### basin-025 — period 3, "trump-" hyphen-cycle
- **Cycle:** `'trump-'` (and rotations)
- **Trajectory:** 15 (`'\n\n\n'` start); captured at length 65.
- **Late-window stats:** H=1.64, gap=5.99
- **Notes:** v0.1-demoted entry now confirmed at depth.

### basin-026 — period 2, `_html` suffix
- **Cycle:** `'_html'`
- **Trajectory:** 18 (`')'` start); captured at length 244.
- **Late-window stats:** H=1.22, gap=3.82

### basin-027 — period 2, `.build` suffix
- **Cycle:** `'.build'`
- **Trajectory:** 21 (`' ('` start); captured at length 409.
- **Late-window stats:** H=0.74, gap=4.92

### basin-028 — period 3, version-suffix `6_v`
- **Cycle:** `'6_v'` (and rotations)
- **Trajectory:** 30 (`'a'` start); captured at length 312.
- **Late-window stats:** H=0.69, gap=4.59
- **Notes:** Cycle-token-id tuple is distinct from basin-023 despite the same `_v[N]` family.

### basin-029 — period 13, Japanese self-support phrase
- **Cycle:** `'、自分の生活を支��することを'`
- **Trajectory:** 37 (`'に'` start); captured at length 80.
- **Late-window stats:** H=2.06, gap=3.35
- **Notes:** v0.1-demoted entry now confirmed at depth. Japanese-only phrase basin; the BOS Japanese hiragana branch resolves into a closed phrase cycle within 80 tokens.

### basin-030 — period 20, google-api-client self-dependency
- **Cycle:** `'.\nThe google-api-client library is a dependency of the google-api-client library'`
- **Trajectory:** 39 (`' ['` start); captured at length 172.
- **Late-window stats:** H=1.76, gap=3.42
- **Notes:** Recursive self-reference ("X is a dependency of X") — clean local-success-trap signature.

### basin-031 — period 18, `file_content` Hello-World assignment
- **Cycle:** `'\n\n# 设置文件内容\nfile_content = \'Hello World!\''`
- **Trajectory:** 40 (`"'"` start); captured at length 134.
- **Late-window stats:** H=1.65, gap=3.58
- **Notes:** This trajectory was assigned to a period-1 `'\n'` basin at v0.1 (K=2 with over-counted reps). Under K=4 + corrected reps it captures into this period-18 phrase basin instead — the v0.1 assignment now reads as a misidentification. The actual asymptotic basin is the bilingual code-comment phrase here.

### basin-032 — period 23, "second approach … different model" methods-section cycle
- **Cycle:** `' second approach is to use the same data as the first approach, but to use a different model.\n\nThe'`
- **Trajectory:** 42 (`' on'` start); captured at length 141.
- **Late-window stats:** H=2.17, gap=3.29
- **Notes:** Methods-section academic-paper boilerplate; closes back to "The" for re-entry.

### basin-033 — period 14, status-table-row fence
- **Cycle:** `'\n+---------------------------------------------------------------+\n| **Status**                                                   |'`
- **Trajectory:** 45 (15-space prefix); captured at length 87.
- **Late-window stats:** H=1.32, gap=4.58
- **Notes:** v0.1-demoted entry now confirmed at depth. Wide ASCII status-table row; tighter than the v0.2 short-fence basins.

### basin-034 — period 19, "simple example" recursive-list
- **Cycle:** `' example of a simple example of a simple example of a simple example of\n *  a simple'`
- **Trajectory:** 46 (`' This'` start); captured at length 122.
- **Late-window stats:** H=1.05, gap=4.39
- **Notes:** Recursive self-embedding ("simple example of a simple example of …"). Strong local-success-trap signature.

### basin-035 — period 18, "not a valid C++ program because" recursion
- **Cycle:** `' is not a valid C++ program. It is not a valid C++ program because it'`
- **Trajectory:** 52 (`' )'` start); captured at length 85.
- **Late-window stats:** H=2.15, gap=3.19
- **Notes:** Same recursive self-justification shape as basin-034.

### basin-036 — period 11, `PchInternal` include cycle
- **Cycle:** `'.h"\r\n#include "PchInternal'`
- **Trajectory:** 54 (`'\r'` start); captured at length 97.
- **Late-window stats:** H=1.24, gap=4.77
- **Notes:** C++ precompiled-header include closure; carriage-return prefix selects MSVC source convention.

### basin-037 — period 23, "list of all the people" credits cycle
- **Cycle:** `'\n\nThe following is a list of all the people who have been involved in the creation of the new website.'`
- **Trajectory:** 55 (`'e'` start); captured at length 93.
- **Late-window stats:** H=1.91, gap=4.92
- **Notes:** Same `"\n\nThe following is a list of all the …"` opener as basin-018 (`files in the project`); a different completion of the same template. Suggests the opener is a strong attractor with multiple closure options.

### basin-038 — period 20, YAML language-list cycle
- **Cycle:** `'\n#   - "fr"\n#\n# language:\n#   - "en"'`
- **Trajectory:** 61 (`'":'` start); captured at length 157.
- **Late-window stats:** H=1.91, gap=3.11
- **Notes:** YAML-comment language-config cycle, alternating `fr` and `en`.

### basin-039 — period 2, `\\string` repeat
- **Cycle:** `'\\string'`
- **Trajectory:** 66 (`' &'` start); captured at length 69.
- **Late-window stats:** H=2.35, gap=2.65
- **Notes:** TeX command-name cycle.

### basin-040 — period 23, PubMed URL cycle
- **Cycle:** `'>\n\n<http://www.ncbi.nlm.nih.gov/pubmed/17371263'`
- **Trajectory:** 68 (`'>'` start); captured at length 92.
- **Late-window stats:** H=0.93, gap=6.30
- **Notes:** A very specific PubMed ID memorized as a cycle target; one of the tightest basins in the catalog.

### basin-041 — period 21, RDoC project sentence cycle
- **Cycle:** `' The RDoC project has been used to develop a set of criteria for the classification of mental disorders.'`
- **Trajectory:** 72 (`' Rele'` start); captured at length 171.
- **Late-window stats:** H=2.04, gap=3.00
- **Notes:** NIMH-related boilerplate; complete-sentence-period closure.

### basin-042 — period 2, `yZ` token alternation
- **Cycle:** `'yZ'`
- **Trajectory:** 73 (`'","'` start); captured at length 196.
- **Late-window stats:** H=2.27, gap=3.64
- **Notes:** Likely base64 / opaque-id pattern.

### basin-043 — period 25, "trade war with China" forum-post cycle
- **Cycle:** `'\njimmy1\nI think the US is the only country that has a trade war with China.\n\n~~~'`
- **Trajectory:** 74 (`' ,'` start); captured at length 255.
- **Late-window stats:** H=1.56, gap=4.95
- **Notes:** Hacker-News-style nested-comment cycle with username and signature delimiter.

### basin-044 — period 2, `.gz` suffix
- **Cycle:** `'.gz'`
- **Trajectory:** 75 (`'/'` start); captured at length 105.
- **Late-window stats:** H=1.70, gap=3.98
- **Notes:** Compressed-archive filename suffix.

### basin-045 — period 26, "joshu" forum signature cycle
- **Cycle:** `"\njoshu\nI'm not sure if this is the best way to do it, but it works.\n\n------"`
- **Trajectory:** 76 (`' :'` start); captured at length 322.
- **Late-window stats:** H=1.30, gap=3.74
- **Notes:** Same nested-comment-with-signature shape as basin-043; different specific contents.

### basin-046 — period 24, `oauth2-tool` repeat
- **Cycle:** `' | ```python3-requests-oauth2-tool-oauth2-tool-oauth2```'`
- **Trajectory:** 78 (8-space prefix); captured at length 177.
- **Late-window stats:** H=0.84, gap=4.98
- **Notes:** Codeblock with hyphenated package-name self-repeat.

### basin-047 — period 22, `Data not found` CSV-format cycle
- **Cycle:** `'.\n\n* **Data not found.** The data in the `.csv` file format is not found'`
- **Trajectory:** 79 (`' +'` start); captured at length 225.
- **Late-window stats:** H=1.99, gap=3.12

### basin-048 — period 2, `class_` prefix
- **Cycle:** `'class_'`
- **Trajectory:** 83 (`' ='` start); captured at length 242.
- **Late-window stats:** H=0.86, gap=5.44
- **Notes:** Identifier-prefix cycle inside code context.

### basin-049 — period 23, "all the files in the directory" build-script cycle
- **Cycle:** `' all the files in the directory.\n\n-   **$** **./build_all.sh** builds'`
- **Trajectory:** 85 (`' builds'` start); captured at length 96.
- **Late-window stats:** H=1.89, gap=3.52
- **Notes:** README-style command-listing cycle.

### basin-050 — period 22, "available options for the download" cycle
- **Cycle:** `'\n\nThe following is the list of all the available options for the download.\n\nDownload\n\nDescription'`
- **Trajectory:** 86 (`' Download'` start); captured at length 89.
- **Late-window stats:** H=1.81, gap=5.05
- **Notes:** Another instance of the `"The following is the list of all the …"` opener family (cf. basin-018, basin-037). Three independent specimens of this template now in the catalog.

### basin-051 — period 16, `--help --help-all` argument cycle
- **Cycle:** `' --help --help-all`\n* `--help-all --help'`
- **Trajectory:** 88 (`'¶'` start); captured at length 116.
- **Late-window stats:** H=1.81, gap=3.17
- **Notes:** CLI help-output cycle alternating two flag orderings.

### basin-052 — period 6, `Error / Key` exception-list cycle
- **Cycle:** `'Error`\n* `Key'`
- **Trajectory:** 99 (`'supset'` start); captured at length 77.
- **Late-window stats:** H=2.56, gap=2.61
- **Notes:** Markdown error-listing cycle.

## Notes across the catalog

- **Phrase basins dominate the new entries.** 25 of the 33 basins surfaced at depth are period-11-or-greater phrase / boilerplate / table-row cycles. The broad-shallow budget=64 regime sees only structural / short-period basins; phrase basins generally need 65–256 additional tokens to lock in. The selection-bias probe makes this regime visible.
- **Recursive self-reference is a common phrase-basin shape.** basin-030 (`X is a dependency of X`), basin-034 (`example of a simple example of a simple example`), basin-035 (`not a valid C++ program because it is not a valid C++ program`) all close by self-quotation. This is exactly the local-success-trap shape described in [ideas.md](ideas.md) "EOS-as-success-signal" — opening invites continuation that contains the opening.
- **The `"The following is a list of all the …"` opener is a meta-attractor with multiple closures.** basin-018 (`files in the project`), basin-037 (`people who have been involved in the creation of the new website`), basin-050 (`available options for the download`) all share the opener and diverge only at the noun phrase. Three template instances from three distinct BOS branches at modest depth.
- **Basin coalescence concentrates in short-period structural basins.** The 33 new basins are all singletons. Coalescence appears to be a property of low-entropy structural attractors (whitespace, table fences, hash fills) rather than phrase content — phrases are too specific to coalesce within a 100-trajectory ensemble at top-100 BOS.
- **Tightness scales with phrase length when the basin closes cleanly.** basin-024 (`.data.cuda`, period 5, gap=7.37, H=0.15) and basin-040 (PubMed URL, period 23, gap=6.30, H=0.93) are tighter than the v0.2 single-character basins. Once a phrase basin commits, it commits hard.
- **39 / 100 trajectories never enter a token-level cycle within L_arch.** They show drifting / serially-numbered output (RFC enumerations, footnote numbers, table rows with incrementing IDs, repeating patches with version drift). These are the territory the v1 cycle-based detector is structurally blind to — see the `882ae6d` observations entry for tail samples and the basin-detection v2 motivation.

## Catalog history

- **v0.1** (commit `ae95f32`, 24 basins / 32 trajectories): post-hoc detection at depth 64 with K=2 confirmation. Detection reported `repetitions_in_cycle_window` as `tail_n // period` (the trivial maximum), not actual consecutive cycle blocks. Five v0.1 entries were not re-confirmed under v0.2 methodology — `-trump` (period-3, traj 15), Japanese phrase (period-13, traj 37), `\n` (period-1, traj 40), status-table-row (period-14, traj 45), and `I had been up` prose-cycle (period-14, traj 3). All were borderline at K=2 and several were explicitly flagged "possibly extended transient" in the v0.1 entries.
- **v0.2** (commit `08b0ba5`, 19 basins / 28 trajectories at broad-shallow budget=64): runtime basin-capture predicate at K=4 confirmation; `repetitions_in_cycle_window` corrected to count actual consecutive cycle blocks back from the tail.
- **v0.3** (commit `882ae6d`, 52 basins / 61 trajectories at L_arch=2048 under selection-bias probe): same predicate as v0.2 but at L_arch budget; probe parameters extended to `max_period=32, cycle_window=256, stats_window=256` to admit longer-period phrase basins. 33 new basins surfaced at depth, predominantly long-period phrase / boilerplate cycles. Of the five v0.1-demoted entries, four (trajectories 3, 15, 37, 45) re-confirmed as proper basins; trajectory 40 captures into a different basin (period-18) than its v0.1 period-1 newline assignment, which now reads as a misidentification. 39 / 100 trajectories remain transient at L_arch — first quantitative evidence that "transient territory" is a substantive region rather than a residue.

---

*Catalog format and basin-id assignment are provisional. Stable basin identity across runs is the cycle-token-id tuple, not the assigned id; assigned ids are for in-document reference only.*
