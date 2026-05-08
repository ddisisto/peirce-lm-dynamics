# Peirce — Literature review (2026-05-08)

*Standalone research output. Conducted to position v0.2 regime vocabulary against existing work before the C2 phase-aware analysis lands. Will be considered alongside the C2 N1 mechanical re-derivation when regime vocabulary enters the working canon.*

*Status: research artifact. May be archived to `archive/` once consumed; until then lives at root.*

---

## Summary

The decoding-quality / degeneration line is large, mature, and almost entirely *engineering-around* in stance. From Holtzman et al. 2019 (1904.09751) onward, the question the literature asks is "how do we sample to avoid degeneration?", not "what is the structure of the degenerate regime?" Nucleus / top-p, locally typical sampling (Meister et al. 2023), η-sampling, mirostat (Basu et al. 2021), contrastive search (Su et al. 2022), DoLa (Chuang et al. 2023), unlikelihood training (Welleck et al. 2020), DITTO / Apple "Learning to Break the Loop" (Xu et al. 2206.02369), and Rep-Dropout (Li et al. 2310.10226) are all in this stance. Theoretical follow-ups (Finlayson et al. 2310.01693 on the softmax bottleneck) sharpen *why* sampling-based fixes work but still treat degeneration as the failure to be averted. None of this work, as far as the survey can tell, analyses the *internal phase structure* of the absorbing regime — it analyses the regime's existence, its rate, and its avoidance.

Three recent papers do treat LM-as-dynamical-system / Markov-chain explicitly: Zekri & Odonnat (2410.02724) "Large Language Models as Markov Chains" proves ergodicity / unique-stationary-distribution at the *token-level* transition kernel; Geng et al. (2603.11228) "Markovian Generation Chains" reformulates iterative whole-text reprocessing as a Markov chain at the *sentence level*, using "recurrent classes / transients" terminology and noting that greedy decoding "typically enters fixed points or short cycles after few steps"; Wu et al. (2502.15208) "Unveiling Attractor Cycles in Large Language Models" is the closest neighbour to Peirce's frame — it explicitly uses "attractor cycle" and a 2-period quantification on iterated paraphrasing in 7B+ instruction-tuned models. None of these three analyse within-cycle template / phase / slot structure; all stop at "cycle exists, here's its period / mixing time / similarity matrix." Mech-interp work (Olsson et al. 2022 induction heads, Singh et al. 2404.07129 induction-head formation, the SAE "Repeat Curse" paper 2504.14218, and Marongiu et al. 2504.01100 "Repetitions are not all alike") sits at the circuit level; the closest contact with slot-readout is the SAE / repetition-features line, but it is investigating *causal mechanism for degenerate behaviour as a defect*, not reading the resulting regime as a probe of the model's prior.

**The headline terminological position.** The Cycle-1 R1 (pinned cycles) / R2 (mode-locked structural attractors) regimes appear to be *implicitly known but not partitioned* by this literature — Geng et al.'s "fixed points or short cycles" covers both; Wu et al.'s 2-period attractor is the simplest case of either. The Cycle-1 R3 (class-enumeration attractor with slot-readout) regime appears genuinely not named in the surveyed literature: no work I could verify partitions degenerate regimes by within-cycle slot-vs-scaffolding decomposition, and no work treats the high-H phase position's alt distribution as a recoverable prior over a nameable class. The closest adjacent work (induction-head pattern-completion, function-vector heads, repetition-feature SAE work) sits at the circuit level rather than at the trajectory-shape level, and is asking different questions. **Recommendation: retain "slot-readout" / "class-enumeration attractor" as project-specific vocabulary with a clean citation neighbourhood; rename or position-against the R1/R2 distinction more carefully because what we call "pinned cycle" and "mode-locked attractor" are token-level vs sentence-level instances of "fixed point or short cycle in the induced Markov chain" (Geng et al.) and we should say so.** Holtzman 2019 is the originator-of-record for context collapse as a phenomenon; its absence of within-cycle structural analysis is the gap Peirce is filling, and that gap should be claimed explicitly rather than implied.

The literature Peirce is most directly in conversation with: Holtzman 2019 (origin), Welleck 2020 + Xu 2022 + Li 2023 (degeneration mechanism), Wu 2502.15208 + Geng 2603.11228 + Zekri 2410.02724 (dynamical-systems / Markov reframings), Olsson 2022 + Singh 2024 (induction-head circuit substrate), and the SAE-based repetition-features work (Marongiu 2504.01100, Yan et al. 2504.14218). Of these, Wu 2502.15208 is the most important to position carefully against — it occupies adjacent vocabulary ("attractor cycle", "dynamical systems view") but at a different scope (iterated paraphrasing of whole texts, not per-step trajectory shape under self-conditioning).

---

## Question 1 — Decoding-quality / degeneration line

The line traces cleanly:

- **Holtzman et al. 2019, "The Curious Case of Neural Text Degeneration"** (arXiv:1904.09751, ICLR 2020). Origin paper. Names the phenomenon (degeneration: incoherent, repetitive output under maximisation-based decoding), identifies the "unreliable tail" of the next-token distribution as the proximal cause, proposes nucleus / top-p sampling as the fix. Verified via fetch. The paper's frame is *avoidance*: sampling from the dynamic nucleus suffices to escape degeneration, so degeneration becomes a quality target rather than an object of further structural analysis.

- **Welleck et al. 2020, "Neural Text Generation with Unlikelihood Training"** (arXiv:1908.04319). Training-side response: penalise repeated tokens during training so the model assigns lower probability to its own repetition. Extends the avoidance frame into the loss function. No within-cycle structural analysis.

- **Su et al. 2022, "Contrastive Search Is What You Need"** (arXiv:2210.14140, TMLR 2023). Decoding-time fix combining model confidence with a "degeneration penalty" defined as max cosine similarity between the candidate's representation and previous-context representations. Connects degeneration to representation-space *isotropy*: when isotropy is high, the degeneration penalty has variance and contrastive search works; when isotropy is low, contrastive search degenerates to greedy. This is the closest the line gets to a structural account of degeneration (it ties the failure mode to a representation-space property), but the analysis is still in service of avoidance.

- **Meister et al. 2023, "Locally Typical Sampling"** (TACL). Frames decoding as targeting samples whose information content matches the conditional entropy — a typicality-band sampling rule. No structural analysis of the degenerate regime per se.

- **Basu et al. 2021, "Mirostat: A Neural Text Decoding Algorithm that Directly Controls Perplexity"** (ICLR 2021). Adaptive truncation that targets a perplexity setpoint via feedback control. Notable for being the closest in spirit to the Cycle-2 N5 idea (cycle-aware sampling) — Mirostat closes a feedback loop on a measurable quantity (running surprisal) and adjusts T accordingly. The Peirce N5 idea differs in driving the feedback signal off shape primitives (osc_amp, per-cycle high-H phases) rather than a fixed perplexity target, but Mirostat is the prior work to cite if N5 ever lands.

- **Chuang et al. 2023, "DoLa: Decoding by Contrasting Layers"** (arXiv:2309.03883, ICLR 2024). Decoding-time fix targeting hallucination, not degeneration directly; works by contrasting late-layer vs early-layer logits. Tangential to the Peirce frame.

- **Xu et al. 2022, "Learning to Break the Loop" / DITTO** (arXiv:2206.02369, Apple). Training-side response identifying *sentence-level self-reinforcement*: each repeat raises the probability of the next repeat. This is the closest the line gets to characterising *why* the model loops — there is a positive feedback at the sentence level. It does not, however, analyse what's *inside* the loop (template structure, phase positions); the analysis is rate-of-repetition and probability-of-continuation only.

- **Li et al. 2023, "Repetition In Repetition Out: Towards Understanding Neural Text Degeneration from the Data Perspective"** (arXiv:2310.10226, NeurIPS 2023). Argues degeneration correlates with repetition rate in training data; introduces Rep-Dropout as a training-time fix. Reframes the explanation from "decoding pathology" to "corpus signal." Still no within-cycle analysis.

- **Finlayson et al. 2024, "Closing the Curious Case of Neural Text Degeneration"** (arXiv:2310.01693, ICLR 2024). Theoretical: proves that truncation methods can guarantee sampled tokens have nonzero true probability *because* of the softmax bottleneck (the model's representation space cannot exactly represent the true next-token distribution and assigns spurious mass to low-probability tokens, which truncation discards). Important because it gives the strongest theoretical reason that nucleus sampling works (not "avoid the unreliable tail" hand-wave but "the softmax bottleneck has measurable consequences and truncation provably avoids them"). Also clarifies that nucleus's success doesn't generalise into a structural account of degeneration — it's still an avoidance result. Verified via fetch.

- **Recent work post-2023.** Marongiu et al. 2025, "Repetitions are not all alike: distinct mechanisms sustain repetition in language models" (arXiv:2504.01100) is the most relevant new entry — it identifies *two* mechanisms behind seemingly identical repetitive behaviour (natural-prompt repetition vs in-context-learning repetition, with different attention-head signatures) and explicitly argues that the same surface behaviour can be sustained by different underlying processes. This is a partition-by-mechanism rather than partition-by-shape, but is structurally aligned with Peirce's claim that the regimes are not interchangeable. Yan et al. 2025, "Understanding the Repeat Curse in Large Language Models from a Feature Perspective" (arXiv:2504.14218, ACL 2025 Findings) uses Sparse Autoencoders to identify "repetition features" causal for the loop. Both verify-via-search; their existence is the strongest signal that the field is currently *opening* the structural analysis of degenerate regimes — Peirce is plausibly aligned with a forming line of work rather than alone in it.

**Synthesis on Q1.** Holtzman 2019 is correctly cited as the originator of context-collapse-as-phenomenon. The decoding-quality line answers "how to avoid" comprehensively but does not partition the regime by shape. The most recent line (Marongiu 2025, Yan 2025) is starting to ask structural questions, but at the circuit / feature level rather than at the trajectory-shape level. The Cycle-1 framing that "simple nucleus sampling cheaply avoids these attractors" is correct in the literal sense — it does — but the inference "therefore the structural analysis is not novel" doesn't follow. The structural analysis was not done; it was made unnecessary for the engineering goal.

## Question 2 — Slot-readout / class-enumeration analogues

This is the central question. I find no direct analogue in surveyed literature.

**Probing-classifier line (closest miss).** Probing classifiers (Hewitt & Manning, Conneau et al., AutoPrompt, etc.) read internal representations or prompt-elicited completions for class structure. They are *task-driven* (probe knows what it's looking for) and *intermediate-representation-based*. Slot-readout is *trajectory-driven* (the structure surfaces in the per-step record without external task) and *output-distribution-based* (the alt distribution at the slot is the readout). The two are not the same operation. A working position: slot-readout is to probing what *unsupervised* discovery of latent classes is to *supervised* probing — the model's own dynamics reveal the class, the analyst doesn't impose it.

**Induction heads (Olsson et al. 2022, transformer-circuits.pub).** Induction heads implement [A][B]…[A]→[B]: scan for the previous occurrence of the current token, copy the next. This is the *circuit substrate* most plausibly responsible for the scaffolding portion of an R3 attractor: the template's fixed positions are exactly what an induction head would re-emit on each cycle. The Cycle-1 R3 readout (slot phase positions admitting class members) is *not* what induction heads do — induction heads copy literally — but the relationship is suggestive: a class-enumeration attractor plausibly composes induction-head scaffolding-copying with some other circuit (function-vector heads? MLP class-embeddings?) that supplies the rotating slot fillers. This is a hypothesis worth flagging but not one I found work testing directly.

**Function-vector heads (Todd et al. 2023, "What needs to go right for an induction head" Singh et al. 2404.07129).** A more sophisticated cousin of induction heads that emerge later in training and embed task-vector-like representations; the recent "Which Attention Heads Matter for In-Context Learning" (arXiv:2502.14010) shows induction heads and FV heads are distinct mechanisms. If R3 attractors decompose into "induction-head scaffolding + FV-head slot filling", this is the place to look for circuit-level corroboration. Not directly stated in any work I fetched.

**Repetition-features SAE line (Yan et al. 2504.14218; Marongiu et al. 2504.01100).** Both papers identify monosemantic SAE features causal for degenerate / repetitive behaviour. Marongiu et al. specifically partition repetitions by attention-head activation signature into "natural prompt" and "ICL" sub-types. This is structurally adjacent to Peirce's R1 vs R2 distinction (different mechanisms behind similar surface behaviour) but partitions on different evidence (head activations vs trajectory-shape metrics). Could be informative for the Peirce N1 analysis if surfaced — the question "do R1 and R2 trajectories share repetition-feature signatures, or differ?" is well-posed and answerable.

**Greedy-cycle / template-instantiation analyses.** Searched "free generation as probing", "unconditional generation language model implicit class", "template enumeration LLM" — none surface directly. Wu et al. 2502.15208 examines iterated *paraphrasing* (text → paraphrase → paraphrase → …) and finds 2-period attractors but does not analyse within-cycle structure. Geng et al. 2603.11228 generalises this to iterated reprocessing under arbitrary prompt templates and finds fixed-points-or-short-cycles under greedy decoding, but again does not partition cycles by within-cycle structure.

**Compositional / template-instantiation work.** I did not surface a clean reference for "language models complete templates with class members" as a free-generation phenomenon. The closest related work is in-context learning's literature (which is conditional and supervised), the cloze-task literature (conditional, masked LM), and the AutoPrompt/probing line (task-supervised). The free-generation, T=0, BOS-only, observe-the-class-the-attractor-rotates-through scenario does not appear to have a named treatment.

**Synthesis on Q2.** *The R3 / slot-readout regime appears genuinely not named in surveyed literature.* The closest neighbours (induction heads, function-vector heads, repetition-features SAE work) are at the circuit level; none reads the slot's alt distribution as the model's prior over an implicit class. The one place where the surface is plausibly opening — Marongiu 2025's "repetitions are not all alike" — partitions by *mechanism* (attention-head signature) rather than by *output shape* (within-cycle template structure with rotating fillers). Peirce's contribution, if it survives the C2 mechanical re-derivation, is to introduce a shape-level partition that is computable read-only over the trajectory and that yields a *measurement instrument* (the alt distribution at the slot) without circuit-level analysis. This is the cleanest claim of novelty in the survey.

The pragmatist guard from foundation.md applies sharply here: the predictive claim ("seed a class-enumeration template, get back a Regime-3 attractor whose slot's alt distribution is the model's prior over the seeded class") is what would substantiate the novelty. It is exactly the C2 N3 (seeded class-enumeration probing) move. Until that lands, "slot-readout as instrument" is an abduction from descriptive evidence on the existing 100 trajectories, not a confirmed claim.

## Question 3 — Dynamical-systems framings

Three papers work at this frame explicitly:

- **Zekri & Odonnat et al. 2024, "Large Language Models as Markov Chains"** (arXiv:2410.02724). Constructs the *token-level* Markov chain induced by an LLM with vocabulary V and context K (state space V^K), proves it is an ergodic unichain with unique stationary distribution, derives mixing-rate bounds and pre-training / in-context generalisation bounds. The relevant claim for Peirce: under appropriate assumptions, the chain converges to a stationary distribution independent of the initial prompt, which "directly explains why LLMs fall into repetitive loops." This framing is *complementary*, not competing — Zekri's stationary-distribution result lives at a higher abstraction than per-trajectory shape; the question of which attractors the trajectory enters and what they look like is the resolution Peirce works at. Verified via search.

- **Geng et al. 2026, "Markovian Generation Chains in Large Language Models"** (arXiv:2603.11228). Sentence-level reformulation: prompt template + previous output → next output, modelled as a Markov chain over text strings. Under greedy decoding, "typically enter[s] small recurrent sets (fixed points or short cycles) after few steps." Uses "recurrent classes" / "transients" / "pre-recurrence phases" rather than attractor / basin / transient. The terminology overlap is partial: Peirce's "transient" matches their pre-recurrence phase; Peirce's "attractor" maps to their recurrent class; Peirce's "basin" has no direct counterpart because they don't partition initial conditions by reached recurrent class. Verified via fetch — they do *not* analyse within-cycle template structure; they analyse the macroscopic "reached fixed point / short cycle / continued production" trichotomy.

- **Wu et al. 2025, "Unveiling Attractor Cycles in Large Language Models: A Dynamical Systems View of Successive Paraphrasing"** (arXiv:2502.15208). Uses "attractor cycle" terminology directly. Setup: iterated paraphrasing T_{n+1} = P(T_n) on Llama-3, Qwen2.5, Mistral, GPT-4o-mini at T=0.6/p=0.9. Operational metric: 2-periodicity degree τ measuring text similarity at lag 2. Finds robust 2-period attractor cycles (T_n ≈ T_{n+2}) across model families and prompts. **Does not address greedy decoding specifically, does not cite Holtzman, does not analyse within-cycle template / phase / slot structure.** Verified via fetch.

These three papers are the closest neighbourhood to Peirce's dynamical-systems framing. None subsumes it: Zekri is one level of abstraction up (token-level transition kernel, stationary distribution); Geng works at the wrong granularity (whole-text iterated reprocessing, not per-step self-conditioning); Wu uses adjacent terminology but at the iterated-paraphrasing scope and at coarse measurement (Levenshtein τ, not within-cycle phase decomposition).

**Position-against-Wu** is the most important: if the survey is read by anyone who knows the literature, "attractor cycles in LLMs" is now Wu's vocabulary. Peirce's claim must explicitly distinguish *per-step in-context* attractors (the fixed-context-window dynamical map under T=0 self-conditioning, which is what Cycle 1 found) from Wu's *iterated-paraphrasing* attractors (a higher-order map on whole texts, which is a different object). Both are dynamical-systems framings of LM behaviour; they do not study the same dynamical system.

## Question 4 — Perturbation in T=0 cycles

Lighter coverage; the experimental shape Peirce's N2 prepares does not have obvious prior art.

- **Xu et al. 2022 (DITTO, 2206.02369)** is the closest: identifies the self-reinforcement mechanism that sustains sentence-level loops (each repeat increases continuation probability). Their intervention is training-time, not the test-time "inject a token mid-cycle and observe" experiment N2 plans.

- **Marongiu et al. 2025 (2504.01100)** does perturb top-p settings to distinguish natural-repetition from ICL-repetition; this is a diagnostic perturbation but not within-cycle token injection.

- **Yan et al. 2025 (2504.14218)** uses SAE feature manipulation to *induce* the Repeat Curse ("Duplicatus Charm") — closer to N2's spirit (intervene at the mechanism level and observe response) but operates on SAE features rather than trajectory tokens.

- I found no work that specifically: (a) takes a trajectory at T=0, (b) identifies a high-H phase position within a stable cycle, (c) injects a chosen alt token at that position, (d) extends from there with KV-cache prefill, (e) reports the cycle's response (re-absorbed, transitioned, broken). This is a clean experimental gap — the engine work is modest, the experimental shape is well-posed, and the results would be informative whichever way they go. The "transient leverage" half (perturb in the early transient and check whether the Regime tag is robust) has weaker prior art still, since most degeneration work doesn't define discrete regimes to be flipped *between*.

The bet for N2: it is a clean experimental contribution if the responses partition meaningfully (e.g. R2 attractors break under any perturbation, R3 attractors re-absorb at the perturbation's phase position). Re-absorption at perturbation phase is, as Cycle 1 already noted, the strongest signature of Regime-3-as-real-attractor; it would also be a clean dynamical-systems result independent of the regime taxonomy.

## Question 5 — Induction heads / Pythia mech-interp

Lighter coverage by design, but the existing literature is rich:

- **Olsson et al. 2022, "In-context Learning and Induction Heads"** (transformer-circuits.pub, arXiv:2209.11895). Establishes the induction-head circuit (previous-token head + induction head) and argues it is responsible for the majority of in-context learning. Pythia models are within scope; the formation of induction heads at ~1B–2B training tokens is a load-bearing data point.

- **Singh et al. 2024, "What needs to go right for an induction head"** (arXiv:2404.07129, ICML 2024). Mechanistic study of induction-head formation in Pythia and other models. Confirms induction heads form abruptly during a training-loss phase change.

- **"Which Attention Heads Matter for In-Context Learning"** (arXiv:2502.14010, 2025). Compares induction heads vs function-vector heads in Pythia models. Induction heads form ~step 1000; FV heads form ~step 16000. Both are causal for ICL. Distinct mechanisms.

- **"LLM Circuit Analyses Are Consistent Across Training and Scale"** (Tigges et al. 2407.10827). Examines circuit consistency across Pythia checkpoints and scales.

**Bearing on slot-readout.** The hypothesis worth flagging: an R3 attractor's scaffolding portion is induction-head copying applied to the established cycle pattern (each scaffolding token has a previous occurrence one period back); the slot portion is supplied by another mechanism (function-vector-style class-conditioned generation? specific MLP factual-recall circuits?). This is consistent with the empirical observation that scaffolding tokens are *literal repeats* across cycles (induction-head signature) and slot tokens *rotate through a class* (a non-induction-head mechanism). I did not find work testing this directly. If the C2 phase-aware analysis lands a clean R3 catalog, this is a follow-up testable in Pythia by ablating heads and observing whether scaffolding survives while slot rotation breaks (or vice versa).

**Pythia-1b specifically.** Most of the Olsson / Singh / Tigges work uses smaller Pythia variants (Pythia-14m through Pythia-2.8b are common). Pythia-1b is in scope but not always highlighted. The Pythia training-checkpoint suite (154 checkpoints) is the lever for any training-dynamics analysis Peirce might want; for the per-step trajectory shape work Cycle 2 is doing, the final checkpoint is sufficient.

## Question 6 — Degenerate regimes as instruments

This question is closest to the *frame* of the project (treating context collapse as phenomenon to characterise, not problem to suppress) and the literature is sparser here than on Q1.

- **The dominant frame remains avoidance.** From Holtzman 2019 through the 2024 truncation-theory work, degeneration is the failure to be averted. Implicit in this frame: the regime is uninteresting once you know how to avoid it.

- **Marongiu et al. 2504.01100** is the strongest counter-example in surveyed work. The paper explicitly argues that *repetition is informative* — distinguishing natural-prompt repetition from ICL-repetition is a diagnostic of which mechanism the model is running. This is "what does the loop tell us about the model" in spirit. It does not, however, treat the loop as a *prior-readout instrument* in the slot-readout sense.

- **Yan et al. 2504.14218** uses degenerate behaviour as a *target* for SAE feature discovery (find the features that cause the Repeat Curse, conclude they exist). This is closer to "the regime is informative about the model" but the information extracted is "which SAE features fire", not "what class does the model think this slot ranges over."

- **Skill-neuron / repetition-feature line.** The recent work showing specialised repetition skill neurons whose activation increases across cycles (referenced in the search but not directly fetched as a single paper) is in this stance: the repetition is a signal of which neurons are running. Again, mechanism-level rather than output-distribution-level.

- **Probing-via-prompting / cloze-task / AutoPrompt line.** Conditioned probing of model knowledge is well-established. The nearest free-generation analogue would be "what does the model say if you start it from BOS" — which is exactly what Peirce's substrate is. I find no work that explicitly analyses BOS-only T=0 trajectories as a *prior-readout instrument* across the model's behaviour.

- **Unconditional generation** in image / diffusion literature (e.g. Li et al. 2312.03701 "Return of Unconditional Generation") is structurally the right neighbourhood (study what the generative system does without conditioning) but lives in a different modality and asks different questions (sample quality, semantic clusters), not "what is the structure of the unconditional attractor."

**Synthesis on Q6.** The instrumental framing of degenerate regimes is *not* the dominant stance in any literature I found. There is movement in this direction — Marongiu 2025 argues repetitions are not all alike and partitions them by mechanism; Yan 2025 uses repetition as a feature-discovery target — but the specific claim "the alt distribution at a slot phase position is a recoverable prior over a nameable class" is not in surveyed work. The closest framing is at the wrong abstraction level (SAE features) or for the wrong purpose (engineering a fix).

This is plausibly the cleanest project-distinctive position. The frame ("treat context collapse as phenomenon to characterise") is mildly counter-current in the decoding-quality literature, mildly aligned with the most recent mech-interp / SAE-feature work, and unique in proposing that *trajectory-shape primitives* (computable read-only over per-step records) are a sufficient surface for the partition.

---

## Terminology implications

**Retain as project-specific.** The vocabulary that names the within-cycle decomposition appears genuinely free of conflicting prior usage in this neighbourhood:

- **Slot / scaffolding / phase position.** Phase position is a standard dynamical-systems term and the local usage is consistent. Slot and scaffolding are project-specific and unconflicted in surveyed literature.
- **Slot-readout.** Project-specific. The closest neighbour in spirit is probing-via-prompting, but the operation differs (free generation, not probe-induced); slot-readout names a distinct thing.
- **Class-enumeration attractor.** Project-specific. No surveyed work names this regime.
- **Measurement instrument** (Regime-3 framing). Project-specific framing of the instrumental stance. Worth retaining.
- **H-trace.** Project-specific shorthand. Unconflicted.
- **Shape primitives** (onset, floor_H, floor_gap, osc_amp, period, gap_over_H). Project-specific operationalisations. Unconflicted.

**Sharpen / position-against.** The vocabulary at the regime / attractor level conflicts with adjacent literature and benefits from explicit framing:

- **Attractor cycle / attractor / basin / trajectory / transient.** Standard dynamical-systems terms. Wu et al. 2502.15208 uses "attractor cycle" for the iterated-paraphrasing case; Geng et al. 2603.11228 uses "recurrent class / transient / pre-recurrence phase" for the iterated-reprocessing case; Zekri et al. 2410.02724 uses "stationary distribution / mixing time" at the token-level transition-kernel abstraction. Peirce should claim "per-step T=0 self-conditioned trajectory under fixed initial condition" as the dynamical system being studied, which distinguishes it from all three. The terminology stays the same; the scope claim is what positions the work.
- **Pinned cycle (R1) and mode-locked structural attractor (R2).** Both are special cases of Geng et al.'s "fixed point or short cycle" at the per-step granularity. Worth keeping the R1/R2 distinction (it's empirically real) but framing as "two within-shape sub-regimes of greedy-decoding fixed-point/short-cycle behaviour", not as if Peirce introduced the cycle phenomenon. **Recommendation: retire "pinned cycle" and "mode-locked structural attractor" as standalone names if they survive to canon, in favour of names that reference the within-cycle distinction directly** (e.g. *single-mode cycle* and *single-mode template cycle* for R1/R2; *class-enumeration template cycle* for R3 — naming the partitioning property rather than coining new genre-names). This is a soft recommendation; the C2 mechanical re-derivation may surface the right names from the data.
- **Crystal.** Cycle-1 sharpened crystal to "Regime-3 attractor" with empirical content. Peirce-internal vocabulary; consider whether the additional name buys anything past "class-enumeration attractor with non-degenerate slot." It may not.
- **Context collapse.** Foundation.md already positions this as continuity with the degeneration literature. Right call. Retain.

**Retire / had been ambiguous.** None obvious. The Cycle-1 retired vocabulary (candidate-basin / window_cap as population axes) is correctly retired. The deprecated-terms checklist in archive/ already covers v0.1 → v0.2 retirements.

**Genuinely novel and worth naming.**

- **Slot-readout** — operation of reading slot alt-distributions across recurrences as the model's prior over the slot's class. Not named in surveyed literature.
- **The R1/R2/R3 partition by within-cycle chosen-token entropy.** Not in surveyed literature. The mechanical statistic (chosen-token entropy across recurrences at a phase position) is what the C2 N1 analysis will compute, and it is the falsifiable seam between the regimes.
- **Measurement-instrument framing.** The instrumental stance toward degeneration is at the edge of current literature (Marongiu 2025) but the specific "alt distribution at slot is class prior" formulation is project-distinctive.
- **Trajectory shape as primary taxonomic surface.** Foundation-level commitment. The closest neighbour is dynamical-systems framings (Zekri, Wu, Geng) which work at coarser shape (period only, similarity matrices, recurrent-class membership). Peirce's six-primitive shape vocabulary (onset, floor_H, floor_gap, osc_amp, period, gap_over_H) is finer-grained and is project-distinctive.

**Headline.** The Cycle-1 vocabulary mostly survives. The R1/R2/R3 names should be considered for renaming to reflect that R1/R2 are sub-cases of well-known greedy-decoding behaviour and R3 is the new addition; the slot/scaffolding/slot-readout sub-vocabulary is the cleanest project-original contribution and the most defensible against literature.

---

## Open questions / further reading

- **Wu et al. 2502.15208 full paper review.** I was able to fetch the HTML and get the abstract / setup / metric, but not exhaustive within-paper detail. If the project ends up citing it heavily, a careful read of section 4–5 (their stability analysis and per-model results) is wanted to be sure the "no within-cycle structural analysis" claim holds in detail.

- **Geng et al. 2603.11228 full paper review.** Same caveat. The paper's "fixed points or short cycles under greedy decoding" is the most direct overlap with Peirce R1/R2; if their treatment includes any partitioning of cycle types, Peirce should cite specifically.

- **Function-vector heads + induction-head composition.** The hypothesis "R3 attractor = induction-head scaffolding + FV-head class-conditioned slot filling" is testable and would be a clean follow-up if the C2 N1 analysis lands. Worth flagging in N4 / a future cycle.

- **"Repetitions are not all alike" Marongiu 2504.01100.** Worth a careful read if Peirce's N1 / N2 work surfaces evidence that R1 vs R2 vs R3 trajectories have different *circuit* signatures; their attention-head methodology is borrowable.

- **Yan et al. SAE Repeat Curse 2504.14218.** If at some point Peirce wants circuit-level corroboration of the regime taxonomy, the SAE-feature intersection with regime tags is worth probing. Their "Duplicatus Charm" induction methodology may also be useful.

- **The Mirostat connection.** If C2 N5 (cycle-aware sampling) ever lands, Mirostat (Basu et al. 2021) is the prior work to position against, since it is the canonical example of feedback-controlled sampling against a perplexity setpoint.

- **Probing-via-prompting alignment.** Whether slot-readout is best framed as "free-generation probing" — a complement to the conditional probing literature — or as a separate operation is a positioning question that may sharpen as the C2 N3 (seeded class-enumeration) work lands.

- **Holtzman 2019 re-read in light of regime taxonomy.** Specifically, Holtzman et al.'s Figure 3 (the human vs greedy entropy/probability comparison) and their qualitative degenerate examples — do their examples land in the R1, R2, or R3 regime under the Cycle-1 taxonomy? If their published examples include R3 specimens that they did not analyse as such, that is the cleanest single piece of evidence that the gap is real.

- **Beyond Pythia-1b.** All claims here are model-agnostic descriptions of the literature; whether the R1/R2/R3 partition holds across model families (Llama, Qwen, Mistral, where Wu 2502.15208 finds 2-period attractors at iterated-paraphrasing level) is downstream empirical work, not within scope of this survey.

---

*Verification status. Papers fetched directly: Holtzman 2019 (search-result level only, abstract verified), Wu 2502.15208 (HTML fetched, setup and metrics verified), Geng 2603.11228 (HTML fetched, framing and greedy-decoding claim verified), Xu 2206.02369 / DITTO (search-result fetched, self-reinforcement claim verified), Marongiu 2504.01100 (HTML fetched, two-mechanism claim verified). Papers cited from search-result snippets only: Welleck 2020, Su 2022, Meister 2023, Basu 2021, Chuang 2023, Li 2310.10226, Finlayson 2310.01693, Zekri 2410.02724, Yan 2504.14218, Olsson 2022, Singh 2404.07129, Tigges 2407.10827. The latter set should be considered "verified by snippet" rather than "verified by full read"; specific quotation-level claims would want a fuller fetch before citation.*
