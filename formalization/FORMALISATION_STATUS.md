# Formalisation status — component level

Provenance: the audit reports in this directory (PROOF_AUDIT,
FORMALIZATION_AUDIT, INCREMENTAL_FORMALIZATION_AUDIT,
CONTINUED_FORMALIZATION_PROGRESS, ARISTOTLE_SUMMARY) were produced against
the manuscript build archived here as `audited_manuscript_v2.pdf`; their
theorem numbers (e.g. Proposition 9.13, condition (95)) refer to that build.
The corrections they mandated are implemented in the current manuscript
(see `paper/CHANGES_AUDIT_v3.md`), where the spectral-growth condition is
now display (75) and the constrained profile MLE is Proposition 9.13 in
corrected form.

Status vocabulary (one label per component, never per theorem):

- `KERNEL_CHECKED` — proved in Lean 4 / Mathlib in this archive, no `sorry`,
  no project axioms; axiom footprint `propext`, `Classical.choice`, `Quot.sound`.
- `PARTIALLY_FORMALISED` — some components kernel-checked, others not.
- `PAPER_PROOF_ONLY` — prose proof in the manuscript; no Lean counterpart.
- `IMPORTED_EXTERNAL_THEOREM` — classical result imported in Part S0 with hypotheses
  verified at the point of use; not re-proved.
- `NUMERICAL_ILLUSTRATION` — illustrated by the seeded replication package;
  illustration is not proof.

A Lean theorem proves the formal proposition supplied to it, not the paper
sentence describing it; the mapping below is the bridge and is maintained
with the archive. No paper theorem is labelled "Lean checked" as a whole.

| Paper result | Component | Lean declaration(s) | Status |
|---|---|---|---|
| Prop 3.1 (exact SCM representation) | pathwise convolution algebra, gauge identity | `Formalization.lean`: operator–forcing gauge identities | PARTIALLY_FORMALISED |
| Thm 3.1(i) (maximal Galerkin rate) | stochastic factorisation, maximal regularity | — | PAPER_PROOF_ONLY + IMPORTED_EXTERNAL_THEOREM (factorisation method) |
| Thm 3.1(ii)–(iii) (integrated/functional convergence) | spectral tail estimates | — | PAPER_PROOF_ONLY |
| Lem 4.1 (fibre criterion) | constancy on observational fibres, descent | `Formalization.lean` fibre criterion | KERNEL_CHECKED |
| Thm 4.1 (exact spectral identification) | scalar drift/scale recovery, transition-summary injectivity, innovation positivity | `Formalization.lean`, `OUMoments.lean` | KERNEL_CHECKED (finite-dimensional core) |
| §4 deconvolution step | characteristic-function cancellation (independence hypothesis stated in text) | `Formalization.lean` cf-cancellation | KERNEL_CHECKED (algebraic core) |
| Prop 4.1 (partial-observation kernel criterion, noise-covariance model) | Gaussian law determined by mean+covariance; kernel conditions on difference sets | finite-dimensional analogues in `Formalization.lean` | PARTIALLY_FORMALISED — infinite-dimensional closure argument PAPER_PROOF_ONLY |
| Prop 9.13 (constrained profile MLE) | clamp formula, profile=joint equivalence, existence, inactivity iff, project-once counterexample | `ExactOULikelihood.lean`, `ConstrainedMLE.lean` | KERNEL_CHECKED |
| Lem 9.5 (score CLT) | exact moments, information identities | `OUMoments.lean`, `OUInformation.lean` | PARTIALLY_FORMALISED — martingale-array CLT IMPORTED_EXTERNAL_THEOREM (Hall–Heyde) |
| Lem 9.6 (LAN remainder) | small-mesh envelope inequalities | `OUSmallMesh.lean` | PARTIALLY_FORMALISED |
| Lem 9.7 (global KL separation) | KL decomposition, psi bounds, burn-in, spectral summation (+ necessity of nonnegativity), scale-ratio perturbation | `GaussianKL.lean`, `OUKLDivergence.lean`, `ModalBurnIn.lean`, `BurnInConstruction.lean`, `SpectralSummation.lean`, `GlobalDriftSeparation.lean`, `GlobalScaleSeparation.lean`, `ScaleRatioBounds.lean`, `ModalKLSeparation.lean` | PARTIALLY_FORMALISED — deterministic chain KERNEL_CHECKED; stochastic uniform control PAPER_PROOF_ONLY |
| Thm 9.13 (consistency) | deterministic argmin separation; clamp inactivity logic | `ArgminConsistency.lean` | PARTIALLY_FORMALISED — fluctuation bounds PAPER_PROOF_ONLY; spectral-growth condition explicit in statement |
| Rate-logic of condition (75) | two-rate non-implication counterexample | `ConstrainedMLE.lean` (`two_rate_conditions_do_not_imply_condition95`) | KERNEL_CHECKED |
| Thm 9.16 (likelihood tails) | chaining lemma written self-contained | — | PAPER_PROOF_ONLY + IMPORTED_EXTERNAL_THEOREM (Hanson–Wright) |
| Thm 9.22 / Lem 9.11 (contact set, no-dominance) | positive-part reductions, 1-Lipschitz sup, fourth-moment no-dominance | `PendingProofCores.lean` | PARTIALLY_FORMALISED — weak convergence and Rosenthal inputs IMPORTED_EXTERNAL_THEOREM |
| Thm 9.26 (floor-studentised bands) | floor-studentised linear + remainder bounds at derivative zeros | `UniformInferenceCore.lean` | PARTIALLY_FORMALISED — conditional bootstrap convergence PAPER_PROOF_ONLY |
| Thm 9.28 (one-sided inference) | floor-rate envelope argument | — | PAPER_PROOF_ONLY (corrected v3) |
| Thm 9.43 (target/derivative approximation) | three-stage triangle assemblies | `PendingProofCores.lean` | PARTIALLY_FORMALISED — analytic tail estimates PAPER_PROOF_ONLY |
| Thm 8.1–8.2 (non-identification) | gauge identities, cross-world variance algebra | `Formalization.lean` | PARTIALLY_FORMALISED — SPDE-level constructions PAPER_PROOF_ONLY |
| Regime scan, coverage tables | seeded Monte Carlo | — | NUMERICAL_ILLUSTRATION (illustration, not proof) |

Negative tests present in the archive (scope-drift detectors):
- project-once profiling counterexample (`projecting_scale_after_unconstrained_profile_can_fail`);
- two-rate non-implication of the spectral-growth condition;
- necessity of termwise nonnegativity in the spectral tail summation
  (`low_mode_nonnegativity_is_necessary`).

Axiom reports: run `#print axioms <name>` per declaration; the archive uses
no project axioms beyond the standard three.
