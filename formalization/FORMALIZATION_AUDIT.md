# Formalisation-first proof audit

## Source and scope

The mathematical source is the 71-page `paper_merged.pdf`.  It contains 79 paragraphs beginning with “Proof.” and a large collection of theorem, proposition, lemma, and corollary statements.  The earlier repository contained no Lean rendering of any of them.

`RequestProject/Formalization.lean` now gives a kernel-checked formalisation of the paper’s foundational finite-dimensional arguments:

- the identification/fibre criterion, including factorisation through the range of the observation map;
- preservation of identification under transport of an identified invariant module;
- characteristic-function cancellation used by the known-error deconvolution argument;
- exact recovery of the scalar spectral drift from `rho = exp (-theta * lambda * delta)`;
- positivity of the OU innovation-variance factor;
- exact recovery of the positive noise scale from its variance;
- injectivity of the positive two-parameter transition summary;
- the operator–forcing gauge identity before and after intervention;
- the variance identity for a cross-world difference and its correlation parametrisation;
- a counterexample showing that unconstrained profiling followed by projection need not agree with constrained profiling.

All declarations in that Lean file compile without `sorry`, `admit`, project axioms, `unsafe`, or `implemented_by`.

## Audit findings

### 1. The paper does not presently contain “complete proofs of every statement”

The PDF explicitly contains **11 occurrences** of the marker `[Verification pending.]`.  They precede or occur within the developments of:

1. Lemma 9.5 (score CLT and observed-information convergence);
2. Lemma 9.6 (uniform local quadratic remainder);
3. Lemma 9.7 (global Kullback–Leibler separation);
4. Theorem 9.13 (consistency of the exact conditional MLE);
5. Theorem 9.16 (polynomial likelihood-ratio bound);
6. the proof following Lemma 9.8 used for that likelihood-ratio bound;
7. Theorem 9.22 (one-sided composite null/contact-set limit);
8. Lemma 9.11 (mode-block no-dominance);
9. Theorem 9.26 (derivative-zero robust simultaneous coverage);
10. Theorem 9.28 (feasible one-sided inference);
11. Theorem 9.43 (target and derivative approximation).

These are not editorially isolated facts: they lie on dependency paths to LAN/efficiency, moment convergence, bootstrap confidence bands, one-sided tests, and the final statistical–numerical error theorem.  Consequently those downstream claims cannot yet be treated as checked consequences of fully verified proofs.

### 2. Finite-sample constrained MLE profiling uses an unjustified step

Proposition 9.13 first computes the **unconstrained** optimum in `sigma²`, minimises the resulting profile over `theta`, and then says to project the resulting scale onto the compact scale interval “when necessary.”  Projection and profiling do not commute in general: when the unconstrained scale optimum is outside the interval, the correct profile objective is the likelihood evaluated at the boundary **for each candidate theta**, and the minimising theta can change.  The paper supplies no special argument showing that the OU likelihood avoids this issue.

The Lean theorem

`OperatorInterventions.projecting_scale_after_unconstrained_profile_can_fail`

provides an exact counterexample for the Gaussian profile objective underlying the profiling calculation.  It exhibits two candidates for which the unconstrained profile prefers candidate A while the lower-bound-constrained objective prefers candidate B.  Thus the stated projection procedure does not follow from the generic Gaussian profiling calculation given in the proof; an additional OU-specific argument would be needed if the authors intend to retain it.

This does not affect an asymptotic argument after one has independently proved that the constraint is inactive with probability tending to one.  It does mean that equations (63)–(64), as written, are not an exact finite-sample construction of the compact-parameter MLE.  A corrected statement should define, for every `theta`,

`v_hat(theta) = projection of RSS(theta)/(N n) onto the permitted variance interval`

and minimise the likelihood with that constrained `v_hat(theta)`.  Only after consistency has been established may one simplify asymptotically to the unconstrained profile with high probability.

### 3. The consistency proof uses a condition absent from its theorem statement

Theorem 9.13 is stated “Under Assumption 9.6,” but its proof begins:

> In addition to Assumption 9.6 we use the spectral-growth condition
> `sqrt(N) * lambda_N = o(Lambda_N)`.

The text then derives this extra condition from Weyl growth in the main model class.  Assumption 9.6 itself, however, does not state Weyl growth or this consequence, and the theorem is presented in the abstract Part S3 regime.  The theorem statement must either add condition (95), explicitly add the relevant Weyl-growth assumption, or provide a proof deriving (95) from its existing hypotheses.  As written this is a hidden assumption in the consistency result and therefore in downstream results that invoke it.

### 4. The paper’s central analytic and asymptotic results are not yet Lean-formalised

The new Lean file deliberately does not encode SPDE existence, stochastic Fubini, factorisation estimates, martingale-array CLTs, LAN, multiplier bootstrap convergence, or semigroup Fréchet differentiability as assumptions.  Doing so would hide rather than check the core burden of the proofs.  These portions therefore remain unformalised, and no claim is made that the entire paper has been machine checked.

## Checks that succeeded

The formalised finite-dimensional core supports the following parts of the paper without exposing a flaw:

- the fibre criterion is exactly constancy on observational fibres and is equivalent to descent through the observation range;
- the positive real scalar semigroup coefficient is injective, so the scalar recovery step has no aliasing;
- the OU innovation factor is positive on the stated positive core;
- the transition summary identifies positive `(theta, sigma)` when `lambda`, `delta`, and `q` satisfy the stated positivity/nonzero conditions;
- known nonvanishing characteristic-function error factors cancel uniquely;
- the operator–forcing gauge calculations are valid additive identities;
- the displayed variance formula for a cross-world contrast is algebraically correct.

## Conclusion

A full formalisation of all 79 proof blocks has **not** been completed.  The formalisation-first pass nevertheless found an unjustified constrained-profiling step, a hidden assumption in the consistency proof, and confirmed several foundational arguments in Lean.  Before downstream asymptotic and inference theorems can be audited conclusively, the 11 explicitly pending proof developments must be completed and the constrained profiling statement must be corrected.