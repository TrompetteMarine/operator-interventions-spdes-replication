# Summary of changes for run 7b6e7d5a-9995-4afa-abd8-864f50532cb1
Continued the proof audit and formalization work.

Completed the remaining proof in `RequestProject/ScaleRatioBounds.lean`:
- Proved `exact_ou_variance_ratio_separated`, showing that compact variance-scale separation survives the exact OU innovation-factor perturbation under the stated mesh and perturbation bounds.
- Removed an unnecessary positivity hypothesis from the theorem statement.
- Verified the theorem uses only standard permitted axioms (`propext`, `Classical.choice`, and `Quot.sound`).

Updated `CONTINUED_FORMALIZATION_PROGRESS.md` to record that the finite-dimensional compact scale-ratio perturbation step is now complete and to state precisely what remains for the full asymptotic Lemma 9.7 assembly.

Verification:
- The complete Lean project builds successfully.
- All project Lean files are free of `sorry`, `admit`, unfinished proof-search commands, and newly introduced axioms.
- Changes were committed and pushed in commit `85f4c64`.

# Summary of changes for run ecbdc5e7-737d-4f16-9708-848364a685bf
Continued the audit and incremental formalization. All retained work was committed, pushed, and the Lean project builds successfully without `sorry`, `admit`, new axioms, or unfinished proof-search commands.

Added:
- `RequestProject/ConstrainedMLE.lean`
  - Correct finite-sample constrained-profile definitions.
  - Proof that pointwise constrained profiling is equivalent to joint constrained minimization.
  - Proof that the Gaussian scale optimizer must be clamped separately for each drift candidate.
  - A Lean-verified abstract rate counterexample showing that `Λ_N → ∞` and `λ_N / Λ_N → 0` alone do not imply condition (95).
- `RequestProject/PendingProofCores.lean`
  - Verified deterministic cores for the contact-set theorem, mode-block no-dominance, and three-stage target/derivative approximation.
- `RequestProject/UniformInferenceCore.lean`
  - Verified floor-studentized linear and remainder bounds that remain valid at derivative zeros.
- `INCREMENTAL_FORMALIZATION_AUDIT.md`
  - The corrected constrained-MLE statement.
  - The required correction to Theorem 9.13: explicitly add condition (95), or a verified sufficient spectral-growth assumption, and refer to the corrected constrained MLE.
  - A theorem-by-theorem status table for all 11 “Verification pending” markers, separating false statements from currently unsupported claims and listing their missing dependencies.
  - Downstream re-check obligations after Theorem 9.13 changes.

Audit conclusions:
- The original “unconstrained profile, then project once” MLE construction is false in general; this is now paired with a verified corrected construction.
- Theorem 9.13’s existing assumptions do not state the extra rate used by its proof. The current formal result verifies failure of the implication between the abstract displayed rates; the audit explicitly notes that a full fixed-spectrum partial-sum counterexample remains a separate construction.
- The other pending SPDE, LAN, likelihood-tail, bootstrap, contact-set, and numerical-approximation theorems are not presently classified as false. They remain unsupported until their listed stochastic and analytic dependencies are formalized.
- Several reusable deterministic dependencies of Theorems 9.22, 9.26, 9.43 and Lemma 9.11 are now machine checked, but are not presented as substitutes for the missing probabilistic or analytic premises.

# Summary of changes for run bca894c7-121c-45a6-909b-be68980faa2c
Added `RequestProject/Formalization.lean`, a sorry-free Lean formalisation of the paper’s foundational finite-dimensional arguments: identification on observational fibres, factorisation through observation ranges, deconvolution cancellation, exact spectral drift/scale recovery, injectivity of the positive transition summary, operator–forcing gauge identities, and cross-world variance algebra. The project builds successfully, and the formalised declarations use no project axioms or unsafe features.

Added `FORMALIZATION_AUDIT.md` with the formalisation-first audit. It records two substantive issues:

1. Proposition 9.13’s finite-sample constrained-MLE construction is not justified: unconstrained profiling followed by scale projection need not equal constrained joint profiling. A Lean-verified Gaussian profile counterexample is included.
2. Theorem 9.13 invokes condition (95), `sqrt(N) * lambda_N = o(Lambda_N)`, although its statement assumes only Assumption 9.6; this is a hidden additional hypothesis unless Weyl growth or (95) is added explicitly.

The report also identifies 11 explicit `[Verification pending.]` markers on dependency paths to LAN, consistency, likelihood-ratio bounds, bootstrap bands, one-sided inference, and statistical–numerical approximation. Consequently, a truthful complete Lean formalisation of all 79 proof blocks is not yet present; the report clearly distinguishes the machine-checked core from the substantial SPDE/asymptotic theory that remains unformalised rather than representing those results through unchecked assumptions.

# Summary of changes for run d4fcb07b-7ef0-401c-b3a8-65561a2ee44c
Audited all Lean source in the repository and added `PROOF_AUDIT.md` documenting the results.

Findings:
- The only Lean file, `RequestProject/Main.lean`, contains imports, namespace openings, and configuration options—but no theorem, lemma, example, instance, or proof declaration.
- No project uses of `sorry`, `admit`, newly declared axioms, `unsafe`, `@[implemented_by]`, or explicit contradiction-elimination constructs were found.
- The project builds successfully under its configured Lean 4.28.0 / Mathlib environment.
- Therefore, there are currently no project proofs susceptible to logical flaws, mathematical errors, circularity, vacuity, or hidden assumptions.

The audit report notes that the external Mathlib dependency was outside the audit scope and that the audit should be repeated after proofs are added.