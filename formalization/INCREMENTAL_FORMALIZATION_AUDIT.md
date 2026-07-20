# Incremental theorem-by-theorem formalization audit

This report continues `FORMALIZATION_AUDIT.md`. It distinguishes a false
finite-sample construction from pending theorems whose conclusions have not
been refuted but whose supplied proofs still rely on unformalized analytic or
probabilistic inputs.

## Corrected constrained MLE statement

Proposition 9.13 must not choose the drift parameter from the unconstrained
profile and then project the chosen scale only once. The correct finite-sample
statement is:

1. for every candidate `theta`, minimize the exact negative log likelihood over
   the permitted compact scale interval;
2. use that *pointwise constrained* minimum as the profile objective;
3. minimize this constrained profile over the permitted drift interval.

Equivalently, if `vHat(theta)` is a constrained scale minimizer for every
`theta`, then choose `thetaHat` to minimize
`objective theta (vHat theta)`. The pair
`(thetaHat, vHat thetaHat)` is then a joint constrained minimizer.

This is formalized without regularity assumptions in
`RequestProject/ConstrainedMLE.lean` by:

- `IsConstrainedScaleMin`;
- `IsCorrectedProfileMLE`;
- `corrected_profile_is_joint_min`;
- `joint_min_is_corrected_profile`.

For a positive one-block Gaussian objective, the pointwise constrained optimum
is the unconstrained optimum clamped to the interval; this is proved by
`gaussian_profile_pointwise_clamp`. The already formalized theorem
`projecting_scale_after_unconstrained_profile_can_fail` is a counterexample to
the original order of operations. Thus the original construction is **false in
general**, not merely unsupported.

## Theorem 9.13 and condition (95)

The proof uses

`sqrt(N) * lambda_N = o(Lambda_N)`

in addition to Assumption 9.6. The displayed clauses
`Lambda_N -> infinity` and `lambda_N / Lambda_N -> 0` do not, as statements
about the two growth scales alone, imply the stronger rate: the sequences
`Lambda_N = N+1` and `lambda_N = sqrt(N+1)` satisfy the former limits while the
strengthened ratio is identically one. This abstract rate calculation is
machine checked by `two_rate_conditions_do_not_imply_condition95`.

That calculation deliberately isolates the rate-logic issue; it is not asserted
to be a spectrum whose partial sum is exactly `N+1`. A fixed monotone spectrum
can also be built with increasingly long plateaux and sparse upward jumps so
that `lambda_N/Lambda_N -> 0` but the strengthened ratio stays bounded away
from zero along the jump subsequence. A full Lean encoding of that block
construction remains to be added. Until either such a derivation is supplied
or the theorem is restricted to Weyl spectra, the audited correction is to add
condition (95) explicitly to Theorem 9.13. Downstream results invoking its
consistency conclusion must inherit that hypothesis (or a verified sufficient
spectral-growth condition).

The consistency theorem also has to refer to the corrected constrained MLE,
not the invalid finite-sample construction in the original Proposition 9.13.
An asymptotic proof may later show that the scale constraint is inactive with
probability tending to one, but that fact cannot be used before consistency has
been established.

## The 11 pending proof markers

The status below is conservative. “Unsupported” means that no counterexample
to the theorem statement has been established, but the present Lean
development does not yet contain the machinery needed to verify its proof.

| Marker | Current status | Main missing dependencies / audit note |
|---|---|---|
| Lemma 9.5, score CLT and observed information | Unsupported, not refuted | Triangular-array martingale CLT, conditional variance convergence, Lindeberg bounds, and normalized Hessian fluctuation bounds for the exact OU array. |
| Lemma 9.6, uniform local quadratic remainder | Unsupported, not refuted | Uniform third-derivative bounds for the exact likelihood plus the observed-information result from Lemma 9.5. |
| Lemma 9.7, global KL separation | Unsupported, not refuted | Uniform OU second-moment lower bounds and compact-uniform control of the Gaussian KL term. |
| Theorem 9.13, consistency | Statement requires correction | Add (95), use the corrected constrained MLE, then prove uniform stochastic equicontinuity and global separation. Every downstream use must inherit these corrections. |
| Theorem 9.16 marker before Lemma 9.8 | Unsupported, not refuted | The theorem depends on the subsequent chaining lemma and global quadratic likelihood bounds. |
| Marker after Lemma 9.8 / proof of Theorem 9.16 | Unsupported, not refuted | Hanson–Wright bounds, coefficient/operator estimates (106)–(108), sub-exponential chaining, and peeling. These estimates are asserted rather than yet derived in Lean. |
| Theorem 9.22, one-sided contact-set limit | Unsupported as a stochastic theorem | Requires weak convergence in `C(T0)`, compactness and local separation. Its strict-null and contact-set deterministic steps are now formalized in `PendingProofCores.lean`. |
| Lemma 9.11, mode-block no-dominance | Unsupported as a moment theorem | Requires martingale Rosenthal estimates and summable initial-condition terms. The deterministic fourth-moment-to-maximum implication is formalized in `PendingProofCores.lean`. |
| Theorem 9.26, derivative-zero robust coverage | Unsupported, not refuted | Requires uniform second-order target expansions, feasible variance/loading convergence, conditional multiplier convergence, and quantile validity. Care is needed because the floor tends to zero; it is not uniformly bounded away from zero. |
| Theorem 9.28, feasible one-sided inference | Unsupported, not refuted | Depends on Theorem 9.26, contact-set separation, conditional quantile convergence, and anti-concentration/regular-boundary conditions. The proof text's claim that the floor is “bounded away from zero” is not justified when `kappa_N,n -> 0`; the argument must instead retain the stated floor-rate normalization. |
| Theorem 9.43, target and derivative approximation | Partially formalized; analytic premises unsupported | The triangle-inequality assembly is formalized by `three_stage_approximation` and `three_stage_derivative_approximation`. Spectral tail estimates, Volterra-kernel derivative estimates, uniform Gaussian chain rules, and prior Theorems 9.40–9.42 remain dependencies. |

## Newly machine-checked proof cores

`RequestProject/PendingProofCores.lean` contains no unchecked assumptions and
proves:

- strict-null positive-part vanishing on a uniform high-probability error event;
- exact positive-part reduction on a contact set;
- the one-Lipschitz property of the positive-part map;
- finite-family fourth-power and fourth-root no-dominance inequalities;
- three-stage target and derivative approximation by the triangle inequality;
- floor-studentized linear and remainder bounds used at derivative zeros
  (`UniformInferenceCore.lean`).

These are dependencies of the pending arguments, not substitutes for their
stochastic or analytic hypotheses.

## Downstream re-check obligations

The following dependency chain must be rechecked after the corrected Theorem
9.13 is completed:

1. MLE asymptotic linearity and normality (Theorems 9.14–9.15);
2. polynomial likelihood tails and moment convergence (Theorems 9.16–9.17);
3. the mixed-rate statistical input used by Part S4;
4. feasible information and multiplier bootstrap results in Part S5;
5. simultaneous bands, one-sided inference, and final statistical–numerical
   error statements.

At this stage these downstream statements are not classified as false. They
are classified as unsupported by the current formal development because their
upstream consistency theorem and several explicitly pending dependencies are
not yet verified.
