# Regime-vocabulary precedent review

*Standalone report supporting `design-reqs.md` "Open: regime vocabulary" closure. Not a naming proposal — naming is adjudicated by the project. Pinned to commit `4309b3e` (HEAD at time of writing). Updated by replacement, not in-place patch.*

*Two priority targets: Geng et al. 2603.11228 ("Markovian Generation Chains in Large Language Models", March 2026) and Zekri et al. 2410.02724 ("Large Language Models as Markov Chains", Oct 2024 / rev. Feb 2025). Both fetched, full PDFs read. The existing `lit-review.md` already places these papers in Peirce's neighbourhood at one paragraph each; this report is the deeper read that goes section-by-section into terminology, formalization scope, and within-cycle structure (or its absence), so that the project lead can adjudicate naming with the actual quotes in hand.*

*The headline finding, stated upfront so the rest of the report serves as evidence: **neither paper decomposes within-cycle structure**. Both treat cycles as atomic — Geng's "fixed point or short cycle / recurrent class" and Zekri's "stationary distribution / recurrent class" both stop at the level of "the chain has entered a recurrent set", with no further partitioning into per-position chosen-vs-varying behaviour. That gap is exactly where Peirce's SLOTTED / SCAFFOLD / NOPERIOD vocabulary lives.*

---

## Geng et al. (2603.11228) — "Markovian Generation Chains in Large Language Models"

**Authors:** Mingmeng Geng, Amr Mohamed, Guokan Shang, Michalis Vazirgiannis, Thierry Poibeau. ENS-PSL & CNRS-Lattice, MBZUAI, École Polytechnique. Submitted March 11, 2026.

### 1. Phenomena named

The paper formalises *iterative reprocessing* of text by an LLM under a fixed prompt template — the operator they study is `s^(t+1) ~ T_{M,ρ,d}(· | s^(t))`, with `s` a single sentence — as a "Markovian generation chain". The phenomena named are:

- **Recurrent set** / **recurrent class.** The chain enters "a small recurrent set" under greedy decoding. Section 3.3, "Regimes under iteration: recurrent classes and transients" — "Empirically, iterative reprocessing exhibits two finite-horizon behaviors: (i) early exact recurrence (a fixed point or short cycle) and (ii) long pre-recurrence phases (continued production of novel surface forms within the iteration budget)." The standard Markov-chain block decomposition (Eq. 7) is invoked: `P` is permuted into recurrent classes `{C_i}` and a transient block `P_tr`.

- **Fixed point** and **short cycle**. Used together throughout, never separately analysed. Section 5.1: "Under greedy decoding, trajectories typically enter small recurrent sets (fixed points or short cycles) after few steps, yielding repeated surface strings or short alternations among near-paraphrases." The paper does not treat fixed-point vs. cycle as two distinct empirical phenomena; the binding is `{fixed-point, short-cycle}` as a joint category vs. `{long pre-recurrence}`.

- **Attractor**, used informally and only twice. Section 5.1: "The observed cycle structure and lexical realizations vary by model, indicating model-specific attractors under a fixed prompting setup." Section 5.3 discussion: "local attractor-like behavior can persist even when the state continues to drift". Not a defined term; their formal vocabulary is "recurrent class".

- **Transient phase / pre-recurrence phase.** Section 3.3: "Small `τ_T` corresponds to early entry into a fixed point or short cycle; large `τ_T` (or T+1) corresponds to a long pre-recurrence phase within `T` steps." `τ_T` is the first-recurrence time, defined as the first iteration index `t` at which `s^(t) = s^(j)` for some `j < t` (exact string equality).

- **Model collapse** is named explicitly *to be distinguished from* — Section 5.4 "Distinction from training-time model collapse" cites Shumailov et al. 2024 and explicitly carves out the inference-time iterative-reprocessing setting from the training-time corpus collapse setting.

There is one verbatim observation about within-cycle behaviour — Table 1 illustrates a 2-cycle: "Qwen2.5-7B enters a 2-cycle after one step, while Llama-3.1-8B alternates between two near-paraphrases with different lexical realizations." The cycle is reported by enumeration of the two surface strings; no per-position decomposition is attempted because the unit of state is the whole sentence, not the per-token slot.

### 2. Within-cycle structure

**No within-cycle decomposition.** The unit of state is `s^(t)`, an entire sentence string. Cycles are detected by exact string equality at the sentence level (Eq. 8). When a 2-cycle is reported (Table 1), it is reported as the pair `{"We begin with a prologue.", "We start with a prologue."}` for Qwen, and the analytical machinery does not look inside the strings to ask which positions are pinned and which are varying.

This is a granularity choice, and the paper is explicit about it. Section 3.2: "We model iterative reprocessing at the sentence level, treating sentence strings as discrete states and the prompted model as a transition operator."

The closest the paper comes to within-cycle structure is the discussion of "lexical realizations" (5.1: "the observed cycle structure and lexical realizations vary by model") and stepwise BLEU/METEOR/ROUGE between successive iterations (Section 5.1, Figure 3), which measure cycle *coherence* but not per-position chosen vs. varying. Stepwise similarity rapidly plateaus under greedy decoding, "consistent with confinement to a small recurrent set rather than continued exploration."

The absence is informative. Geng et al. would describe Peirce's SLOTTED-CLASS, SLOTTED-COUNTER, SLOTTED-MIXED, and SCAFFOLD trajectories *all* as "the chain has entered a small recurrent set / fixed point or short cycle" with no further partition. The within-cycle vocabulary Peirce uses (slot, scaffolding, slot-readout) has no precedent term in this paper.

### 3. Naming conventions used

Predominantly **Markov-chain genre**: "Markov kernel", "transition matrix", "recurrent classes", "transient block", "stationary distribution", "first recurrence time", "kernel composition", "doubly stochastic", "KL contraction". The paper names the conceptual move as "drawing a Markov-chain framing of iterative reprocessing", and the language stays inside that genre throughout.

**Dynamical-systems genre is borrowed sparsely and informally.** "Attractor" appears twice, both times qualified ("model-specific attractors", "local attractor-like behavior"). "Trajectory" appears as `{s^(t)}` — a sequence of states under iteration of an operator. No use of "basin", "periodic orbit", "phase space", or "fixed point" as a dynamical-systems term (their "fixed point" is the Markov-chain notion: a state `s` with `P(s,s) = 1` under deterministic decoding, equivalently a 1-cycle).

**Decoding-quality genre appears in the related-work scaffolding.** Section 2 cites Holtzman 2019 ("The Curious Case of Neural Text Degeneration") in the context of "sampling and diversity in LLM-generated content". Top-k (Fan 2018), top-p (Holtzman 2019), and softmax bottleneck (Chang & McCallum 2022) are cited as the sampling-fixes line. The paper itself does not adopt "degeneration" or "repetition" as primary vocabulary — it adopts "rapid convergence to fixed points or short cycles" instead, which is a deliberate dynamical-systems-flavoured restatement of the same phenomenon.

### 4. Cross-reference Peirce's tags

| Peirce tag | Geng-paper alias | Comment |
|---|---|---|
| **SLOTTED-CLASS** | "small recurrent set" / "fixed point or short cycle" | Geng has no name for the within-cycle slot phenomenon; a Peirce SLOTTED-CLASS trajectory at the per-token level would, at the *sentence* level Geng works at, present as a recurrent set whose cardinality is the slot's class enumeration count. The class-enumeration phenomenon would be partly absorbed (each sentence in the recurrent set is itself a complete enumeration), partly invisible (the per-token slot prior is below their granularity). |
| **SLOTTED-COUNTER-INT / -LETTER** | "small recurrent set" / "fixed point or short cycle" | Same as above. A counter-rotation at the token level (1, 2, 3, …) would manifest at the sentence level as a long cycle if the counter-context is preserved across iterations. Geng's framing would not distinguish this from a class-enumeration cycle. |
| **SLOTTED-MIXED** | "small recurrent set" | No alias; this is a multi-slot within-cycle phenomenon and Geng has no within-cycle vocabulary. |
| **SCAFFOLD** | "fixed point" (period 1) or "short cycle" with period N | If the SCAFFOLD trajectory's period is 1 at the sentence level, it would be Geng's "fixed point" — and Geng *would* call this exactly that, though the underlying Markov-chain definition (`P(s,s)=1` under deterministic decoding) is what they mean rather than a per-token notion. If the scaffold has cycle length > 1 at the per-token level, again no sentence-level alias would distinguish it from a SLOTTED cycle of the same period. |
| **NOPERIOD** | "long pre-recurrence phase" or "continued production of novel surface forms" | Geng's `τ_T = T+1` case (no exact repeat within the budget) is the closest alias. Important nuance: their NOPERIOD is at the *finite-horizon* sentence-level granularity, while Peirce's NOPERIOD is at the per-step H-trace autocorrelation granularity within a single trajectory. The phenomena are not the same; both are "no detected period" but they live at different scales. |

The honest summary: Geng's vocabulary aliases SLOTTED, SCAFFOLD, and (loosely) NOPERIOD all to the same coarse partition "{fixed point or short cycle} vs {long pre-recurrence}", because the paper works at sentence-level state and finite-horizon recurrence. Within Peirce's six-tag partition, exactly **one** of Geng's distinctions survives: the "is there an exact recurrence at all" axis, which is roughly Peirce's PERIODIC vs. NOPERIOD. The within-PERIODIC sub-partition (SLOTTED-* vs. SCAFFOLD) has no precedent name in this paper.

### 5. Code repos

**No code repository linked or findable.** The paper has no "Code availability" statement. References include Karpathy's minGPT GitHub link, but only as a citation for a baseline. A web search for "Markovian Generation Chains Geng github" surfaces no project repo. Author email contact would be the path to source if needed.

---

## Zekri et al. (2410.02724) — "Large Language Models as Markov Chains"

**Authors:** Oussama Zekri, Ambroise Odonnat, Abdelhakim Benechehab, Linus Bleistein, Nicolas Boullé, Ievgen Redko. ENS Paris-Saclay, Huawei Noah's Ark Lab, Inria, Eurecom, Imperial College London. Submitted Oct 3 2024, revised Feb 2 2025.

### 1. Phenomena named

The paper builds the **token-level** Markov chain induced by an LLM with vocabulary `V` (size `T`) and context window `K`. The state space is `V_K* = {v ∈ V*, |v| ≤ K}` — all sequences of at most `K` tokens, of size `|V_K*| = T(T^K - 1)/(T - 1)`. The transition matrix `Q_f` has `Q_f(v_i, v_j) = {f_Θ(v_i)}_{j_0}` if `v_j` is a compatible next-step extension of `v_i` (concatenation of one token), else 0 (Proposition 3.2). Section 3.1.

The phenomena named:

- **Stationary distribution** `π`. Definition C.3: "A distribution `π` on `Ω` is said to be a stationary distribution if the action of the transition kernel leaves it invariant." Proposition 3.4 establishes that `MC(V_K*, Q_f)` is an ergodic unichain, so `lim_{n→∞} Q_f^n = e π^T` — the chain converges to a unique stationary distribution independent of the initial state.

- **Recurrent class / transient class.** Definition C.5 (Recurrent and transient states): "For finite-state Markov chains, a recurrent state is a state `i` that is accessible from all states that are accessible from `i`". The Markov chain induced by an LLM has at most one recurrent class (the "blue block" in Figure 2) plus transient states (the "green blocks"). Theorem C.9 invoked: "either all states in a class are transient or all are recurrent."

- **Aperiodicity.** Definition C.7: "The period of a state `i`, denoted `d(i)`, is the greatest common divisor (gcd) of those values of `n` for which `Q^n(i,i) > 0`. If the period is 1, the state is aperiodic." Section 3.1 proves `MC(V_K*, Q_f)` is ergodic, which requires aperiodicity. The proof of aperiodicity (Section F context, around line 2098) goes: "transition probabilities do not depend on a specific cycle, and Thanks to Theorem C.9, it means that the whole class `R` is aperiodic."

- **Mixing time** `t_mix(ε)`. Definition C.8: "The mixing time `t_mix(ε)` of a Markov chain is the minimal time needed to be `ε`-close to its stationary distribution". Used to characterise convergence speed.

- **"Looping"** (informal). Section 3.1, the discussion under Proposition 3.4: "**1. Looping.** The stationary distribution is independent of the initial state (i.e., input prompt), and reaching it should send the LLM into a deterministic loop of repetitions. This behavior is well known and occurs frequently in practice with many existing LLMs (Ivgi et al., 2024), requiring adding a repetition penalty." This is the closest the paper comes to naming a Peirce-relevant phenomenon, and the cited work is Ivgi et al. "From loops to oops: Fallback behaviors of language models under uncertainty" (2407.06071).

- **Coherence / temperature pathology.** "**2. Temperature and coherence.** Increasing temperature of the model leads to a decreasing coherence of its outputs as measured by perplexity (Peeperkorn et al., 2024). Temperature, in turn, impacts `ε`... increasing the temperature increases the speed of convergence to the stationary distribution making the output less coherent."

The paper's main theoretical contribution is *generalisation bounds* (sample complexity, in-context learning bounds) derived from this Markov-chain framing — the dynamical-systems content of the paper is largely Section 3 (~6 pages); Sections 4–5 are about pre-training and ICL bounds. For Peirce's purposes, only Section 3 is directly relevant.

### 2. Within-cycle structure

**No within-cycle decomposition.** The chain is studied at the abstraction of "ergodic unichain → unique stationary distribution → mixing time bound". The paper does not analyse the *shape* of a sample trajectory at all — there are no per-step records, no per-position analyses, no examination of which positions in a cycle are pinned vs. varying. The dynamical analysis is pitched at one level higher than Peirce's: Peirce reads the per-step `s^(t)` sequence; Zekri reads the asymptotic distribution `π`.

In the toy-model illustration (Section 3.2, Figure 4 — a binary-sequence parity model with `T=2, K=3`), the analysis renders the transition matrix `Q_f` directly as a 14×14 grid and the stationary distribution `π` as a histogram over the 14 states. There is no concept of "phase position within a cycle" or "position whose chosen token varies across recurrences" — the 14 states *are* the 14 sequences of length ≤ 3, and dynamics on them are summarised by `Q_f^n → e π^T`.

The paper would describe a Peirce trajectory only as: "the chain has converged to its recurrent class" (the blue block in Figure 2) or "the chain is still in the transient class" (a green block). Once in the recurrent class, the only further structure named is the rate at which `Q_f^n(i, ·)` approaches `π`, characterised by `ε = min_{i,j ∈ R^2} {(Q_f^K)_{i,j}}` — the smallest non-zero element of the K-th power of the transition matrix restricted to the recurrent class. This `ε` is a global scalar property of the chain; it is not a per-position quantity and it does not partition states within the recurrent class.

The crucial point for Peirce's naming question: Zekri's framework cannot distinguish a SCAFFOLD trajectory (every position pinned) from a SLOTTED-CLASS trajectory (one position varying across recurrences) without leaving the framework, because both are "trajectories whose state-distribution converges to `π`" at the level of analysis the paper conducts.

### 3. Naming conventions used

Almost entirely **Markov-chain / measure-theoretic genre**, drawn from standard references (Paulin 2015, Roberts & Rosenthal 2004): "Markov chain", "transition kernel", "stationary distribution", "ergodic unichain", "aperiodic class", "mixing time", "Marton coupling", "total variation distance". The presentation is mathematical-statistics-flavoured; the genre is set by Section 2 ("Background Knowledge: Markov chains").

**Dynamical-systems vocabulary is essentially absent.** "Attractor", "basin", "periodic orbit", "fixed point" (in the dynamical-systems sense), "phase space" — none of these appear. "Fixed point" appears once in passing in a related-work context ("`x_{i+1} = f(x_i)`") referring to a different paper (Li et al. 2023). The genre is Markov-chain rigorous, not dynamical-systems-borrowed.

**Decoding-quality / repetition vocabulary appears only as informal discussion.** "Repetitions" is mentioned once in the abstract ("pathological behavior observed with LLMs such as repetitions and incoherent replies"). "Looping" is the section heading for the Proposition 3.4 implication discussion. "Repetition penalty" is mentioned in passing. But these are not the primary terminology of the paper.

**Holtzman 2019 is not cited.** This is notable — the paper explicitly relates its theory to "the pathological behavior observed with LLMs such as repetitions" but does not cite the foundational decoding-degeneration paper. Their citation for repetition behaviour in practice is Ivgi et al. 2024 ("From loops to oops"). Welleck and the unlikelihood-training line are also not cited.

### 4. Cross-reference Peirce's tags

| Peirce tag | Zekri-paper alias | Comment |
|---|---|---|
| **SLOTTED-CLASS** | "trajectory has reached recurrent class" / "looping" | Zekri's framework does not distinguish slot vs. scaffold within a recurrent class; a SLOTTED-CLASS trajectory and a SCAFFOLD trajectory are both just "in the recurrent class". The class-enumeration phenomenon (the slot's alt distribution as a prior over a nameable class) has no Zekri analogue at all — Zekri's analysis would compute the marginal of `π` over the slot position, but the framework provides no language for *reading* that marginal as a class prior. |
| **SLOTTED-COUNTER-INT / -LETTER** | "trajectory has reached recurrent class" | Same as above. A counter-slot is a recurrent class with structure that Zekri's framework does not name. The integer / letter sequence-structure is invisible at this abstraction level. |
| **SLOTTED-MIXED** | "trajectory has reached recurrent class" | Same — no within-class differentiation. |
| **SCAFFOLD** | "trajectory has reached recurrent class" / "absorbing state" (informally) | A SCAFFOLD with cycle period 1 at the per-token level would be a fixed point of `Q_f` in the Markov-chain sense — a single state `v` with `Q_f(v, v') > 0` for some single `v' = [v[1:], v[k]]` that is itself fixed under further application. Zekri does not use "absorbing state" as a term but the concept is implicit. A SCAFFOLD with period > 1 would not be a fixed point in `Q_f`; it would be a recurrent class with cyclic structure, but Zekri's setup proves the chain is aperiodic, so the cyclic structure must be "absorbed" into the multi-state recurrent class — which is exactly how their framework would describe SCAFFOLD with period > 1: as a multi-state aperiodic recurrent class. The aperiodicity requirement is interesting: Peirce's SCAFFOLD trajectories with period > 1 would, at the token-level Markov chain Zekri studies, be aperiodic *only* under the definition that "period" is taken across all `n` for which `Q^n(i,i) > 0`, which holds for context-window-restricted chains because of the deletion process. So Zekri's chain is aperiodic by construction; SCAFFOLD's per-token cycle structure is invisible at this granularity. |
| **NOPERIOD** | "trajectory still in transient class" / "slow mixing" | A NOPERIOD trajectory in Peirce's sense is one whose deep-window H-trace autocorrelation has no detected peak above threshold. Zekri's analogue would be a trajectory that has not yet reached the recurrent class within the observation horizon — which is the transient phase. The phenomenon Peirce calls NOPERIOD might *also* manifest as a recurrent class with cycle period longer than the autocorrelation lag-window allows, in which case Zekri would call it "in the recurrent class but at a long mixing time". Either way, no precise alias. |

The summary for Zekri: the paper's framework is at *one level of abstraction higher* than Peirce's per-trajectory shape work. It proves that the LLM-induced Markov chain has a unique stationary distribution and bounds the mixing time, but it does not look at sample trajectories. Peirce's SLOTTED / SCAFFOLD / NOPERIOD partition lives entirely *within* what Zekri would call "the structure of the recurrent class" or "the transient-class behaviour", and Zekri's paper does not partition either.

### 5. Code repos

**No code repository linked or findable.** No "Code availability" statement in the paper. The only `github.com` URL in the bibliography is Karpathy's minGPT, cited as a baseline for the toy model. A check of the corresponding-author's web page (`ambroiseodt.github.io`) confirms no code repo for this paper. A direct web search returns the arXiv, OpenReview, and Hugging Face Papers entries but no source-code link. Author email contact would be the path if needed.

---

## Synthesis: precedent map for Peirce's tags

The literature partition is coarser than Peirce's at every level. Treating "appears as a named phenomenon in Geng or Zekri" as the bar:

| Peirce tag | Precedent name | Where |
|---|---|---|
| **SLOTTED-CLASS** | Not named in surveyed literature. | Both papers stop at "recurrent class / fixed point or short cycle". |
| **SLOTTED-COUNTER-INT** | Not named in surveyed literature. | Same. The counter-rotation phenomenon is not isolated as a sub-type. |
| **SLOTTED-COUNTER-LETTER** | Not named in surveyed literature. | Same. |
| **SLOTTED-MIXED** | Not named in surveyed literature. | Same. |
| **SCAFFOLD** | "fixed point or short cycle" (Geng); "recurrent class" (Zekri); informally "looping" / "deterministic loop of repetitions" (Zekri). | At Geng's sentence-level granularity, a SCAFFOLD is just "fixed point or short cycle". At Zekri's token-level Markov chain, a SCAFFOLD is "in the (multi-state, aperiodic) recurrent class". |
| **NOPERIOD** | "long pre-recurrence phase" (Geng); "transient class" / "slow mixing" (Zekri). | Both aliases are at different scales than Peirce's autocorrelation-based NOPERIOD; the closest Markov-chain alias is "trajectory has not yet reached the recurrent class within the observation horizon". |

**Reading.** The within-cycle / template-structure axis on which Peirce partitions SLOTTED vs. SCAFFOLD does not appear in either paper. This is consistent with the project's existing `lit-review.md` claim that "the slot / scaffolding / slot-readout / class-enumeration-attractor neighbourhood appears genuinely unnamed in surveyed literature." The two priority targets confirm that conclusion at the level of detail this report extracts.

What *is* named in the surveyed literature, and would alias to a coarser axis Peirce maintains:

- **PERIODIC vs. NOPERIOD** (Peirce's "is there a detected period" axis at the trajectory level) ↔ "fixed point or short cycle" vs. "long pre-recurrence phase" (Geng) ↔ "in the recurrent class" vs. "in the transient class / slow mixing" (Zekri). Caveats: the granularities are different (sentence-level vs. token-level) and the detection methods are different (exact string equality, mixing time, autocorrelation peak), so the alias is conceptual rather than identical.

- **SCAFFOLD with period 1** (per-token argmax-fixed-point — the trajectory is a single repeated token forever) ↔ "fixed point" of the Markov chain (Geng's `s` with `P(s,s)=1`; Zekri's `Q_f(v,v')>0` only for `v' = v` after deletion). Here the alias *is* nearly identical at the per-token level — a SCAFFOLD with period 1 *is* a Markov-chain fixed point under Zekri's `Q_f`.

What is *not* named anywhere in the surveyed literature:

- The slot-vs-scaffolding partition within a cycle.
- The slot-readout operation (reading the slot's alt distribution as the model's prior over the slot's class).
- The distinction between class-slot and counter-slot specimens (SLOTTED-CLASS vs SLOTTED-COUNTER-*).
- The mixed-slot specimen (SLOTTED-MIXED).
- Any per-step shape primitive in the per-trajectory `H`-trace sense (entropy floor, oscillation amplitude, autocorrelation peaks).

The naming-decision implication, for the project lead to weigh: the within-cycle vocabulary (slot, scaffolding, slot-readout, class-enumeration attractor) has no precedent that needs to be aliased-to or distinguished-from. The taxonomy *tags* (SLOTTED-CLASS, SCAFFOLD, NOPERIOD, etc.) are not at risk of clashing with prior names, because no prior names exist for the partition they implement. However, the *coarse* axis (PERIODIC vs. NOPERIOD; SCAFFOLD-period-1 ≈ "fixed point") has well-established Markov-chain genre vocabulary, and naming choices that imply Peirce introduced the cycle phenomenon itself would mis-credit standard Markov-chain results. That risk applies most strongly if any name in the proposed taxonomy is read as claiming priority on "trajectories enter cycles" — which is well-known. The within-cycle decomposition is the project-distinctive contribution.

## Code repos

- **Geng et al. 2603.11228** — no public code repository found. Paper has no code-availability statement. Web search returns no project repo.
- **Zekri et al. 2410.02724** — no public code repository found. Paper has no code-availability statement. Corresponding-author's web page does not list a repo for this paper. Karpathy's minGPT is cited as a baseline but is not their code.

If the project wants to compare against either paper's empirical setup (Geng's iterated-rephrasing `τ_T` measurement, or Zekri's mixing-time scaling experiment with Llama / Gemma families), implementation would have to be from-scratch from the descriptions in the papers. Both papers' empirical setups are fully described in their respective Methods / Experimental Setup sections, so reproduction is feasible without source code, though tedious.

## Open questions / things the survey couldn't settle

- **Exact "fixed point" terminology in Geng's Markov-chain formalism.** Geng uses "fixed point" both as a Markov-chain technical term ("a state `s` with `P(s,s) = 1` under deterministic decoding") and informally as a synonym for "1-cycle of the iteration map". In their setting these are equivalent (deterministic decoding makes the chain a deterministic dynamical system on sentence space, where Markov-chain fixed points and dynamical-systems fixed points coincide), but a careful naming pass should note that the term carries both connotations in their text.

- **Whether either paper's notion of "period" is meaningful at Peirce's per-token granularity.** Zekri's chain is aperiodic by construction (the deletion process gives `Q_f^n(i,i) > 0` for various `n`), so the Markov-chain "period" (gcd of return times) is 1 trivially. This is *not* Peirce's "period" (autocorrelation peak in deep-window H-trace). Naming-wise, "period" already has at least three meanings in the neighbourhood: Markov-chain period (gcd of return times), dynamical-systems period (cycle length under iteration), and Peirce's autocorrelation period. The current `design-reqs.md` flagged-convention treatment of `period` is well-positioned for this; the report notes the ambiguity exists in the literature too.

- **Geng's "fraction of cycles that are exact" vs. Peirce's "fraction of phase positions that are pinned".** Geng's Appendix Table 3 reports the fraction of chains with no exact repetition within `T = 50`. This is a statistic about *trajectory population*; Peirce's "fraction of phase positions pinned" is a statistic about *within-trajectory structure*. The two are not the same and could be conflated in readers carrying the Geng frame to the Peirce work. Worth being explicit about which axis any "fraction" refers to.

- **What "attractor" means across the surveyed neighbourhood.** Geng uses "attractor" twice, informally and as decoration on "recurrent class". Zekri does not use it. Wu et al. 2502.15208 (already in `lit-review.md`, not re-fetched) uses "attractor cycle" centrally for the iterated-paraphrasing case. Peirce's foundation defines "attractor" as a region of phase space that trajectories enter and remain in. The four uses are coherent at the conceptual level — all name the "trajectories enter and stay in a stable region" idea — but the granularities differ (sentence-level decoration in Geng; absent in Zekri; iterated-paraphrasing-cycle in Wu; per-step trajectory in Peirce). The project's own term is well-grounded; naming choices that clarify the granularity (e.g. "per-step token-level attractor" rather than just "attractor" when contrasting with prior work) would reduce ambiguity. Not a finding the report can settle — just an observation for the naming pass.

- **Whether Welleck 2019 / Holtzman 2019 within-cycle examples include class-enumeration specimens.** The existing `lit-review.md` flags this as a Holtzman re-read item. Out of scope for this report (the two priority targets did not cite Welleck and Geng cited Holtzman only as a sampling-methods reference without engaging the qualitative-degenerate-examples content). The Holtzman re-read is an independent open thread.

- **The Ivgi et al. 2024 "From loops to oops" paper, cited by Zekri as the in-practice reference for repetition.** Not fetched here; arXiv:2407.06071. Its title — "fallback behaviors of language models under uncertainty" — suggests it might decompose loop behaviour at a finer granularity than either Geng or Zekri. If true, this would be a more direct precedent than either of the priority targets. Worth a follow-up fetch in a subsequent precedent pass; flagging here so it does not get lost.
