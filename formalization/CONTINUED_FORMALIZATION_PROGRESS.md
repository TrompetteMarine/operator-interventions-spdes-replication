# Continued theorem-by-theorem formalization and audit

This report continues, but does not replace, the earlier audit reports. It records only results checked in the current continuation.

## Dependency graph

| Layer | Lean declaration | Depends on | Status |
|---|---|---|---|
| Exact transition | `ouRho`, `ouInnovationFactor`, `ouResidual` | real exponential and finite paths | Defined |
| Positivity | `ouInnovationFactor_pos`, `ouModalVarianceFactor_pos` | `spectralH_pos` | Proved |
| Exact likelihood | `exactOUNegLogLikelihood`, `exactOUNegLogLikelihood_decomposition` | residuals, finite sums, positivity | Proved |
| Pointwise scale profile | `exactOU_pointwise_constrained_scale` | exact decomposition, Gaussian clamp theorem | Proved, including zero RSS |
| Constraint inactivity | `exactOU_scale_constraint_inactive_iff` | order properties of `min`/`max` | Proved |
| Corrected joint MLE | `exactOU_corrected_profile_is_joint_min` | pointwise constrained scale theorem | Proved |
| Finite-sample existence | `exactOU_joint_min_exists` | compact parameter rectangle and continuity of the exact likelihood | Proved |

## Proposition 9.13: exact finite-dimensional correction

**Paper item:** Proposition 9.13, exact profile likelihood.

**Lean file:** `RequestProject/ExactOULikelihood.lean`.

**Audited statement:** The parameter called `v` in Lean is the variance scale `σ²`. For each drift candidate `θ`, the exact twice-negative conditional log likelihood is minimized over the compact variance interval by

`max lower (min upper (RSS(θ)/(N*n)))`.

Only after this pointwise constrained minimization may the drift profile be minimized. The resulting pair is a joint constrained minimizer. A minimizer exists on the compact drift/variance rectangle whenever the exact modal variance factors remain positive.

**Corrections:** The paper's unconstrained drift profiling followed by one final scale projection is not used. The corrected theorem clamps separately at every drift candidate. The inactivity theorem says precisely that clamping does nothing iff the unconstrained scale belongs to the compact variance interval; it makes no appeal to consistency.

**Dependencies:** All project-local dependencies of these finite-sample results are proved. The proofs use only standard Mathlib principles. They do not prove the paper's subsequent probabilistic claim that inactivity occurs with probability tending to one.

## Theorem 9.13: consistency

**Status:** Still unsupported, with a corrected statement required.

The exact finite-sample likelihood and constrained MLE layer is now available. The full consistency theorem still requires global KL separation and uniform stochastic likelihood control. Its statement must explicitly assume condition (95), `sqrt(N) * lambda_N = o(Lambda_N)`, unless that condition is derived from a stated spectral hypothesis. The earlier abstract two-rate example remains evidence only at the rate-logic level; a fixed positive monotone partial-sum spectrum violating (95) has not yet been machine checked.

## Pending theorem status

None of the 11 paper proofs marked “Verification pending” is newly classified as complete by this layer. This work discharges finite-sample exact-likelihood and compact-argmin dependencies for corrected Theorem 9.13. Lemma 9.7, stochastic uniform control, and the full consistency conclusion remain unproved. All LAN, likelihood-tail, contact-set stochastic, bootstrap, robust-inference, and SPDE approximation statuses remain as recorded in `INCREMENTAL_FORMALIZATION_AUDIT.md`.

## Lemma 9.7: Gaussian KL analytic layer

**Lean files:** `RequestProject/GaussianKL.lean` and `RequestProject/OUKLDivergence.lean`.

The following dependencies are now proved:

- nonnegativity of `ψ(x) = x - 1 - log x` for `x > 0`;
- its exact zero set on the positive half-line;
- a strictly positive compact-uniform lower bound away from `x = 1`;
- the exact scalar Gaussian KL decomposition into variance-ratio and squared-mean terms;
- nonnegativity and equality characterization for scalar and finite sums of Gaussian KL terms;
- specialization to the exact finite-modal OU conditional experiment;
- nonnegativity, exact decomposition, and zero characterization of the finite OU conditional KL;
- finite-sample identification of drift and variance scale when one positive-frequency mode has a nonzero lagged observation.

This completes the elementary finite-dimensional KL and identification core, but not paper Lemma 9.7 itself. The paper's global asymptotic lower bound still needs uniform modal second-moment lower bounds and conversion of finite conditional contrasts into a bound of order `Λ_N`, uniformly outside an `ε`-ball. No such stochastic or asymptotic premise has been encoded as a conclusion.

## Exact OU moments and information layer

**Lean files:** `RequestProject/OUMoments.lean` and `RequestProject/OUInformation.lean`.

The following exact finite-dimensional dependencies are now machine checked:

- the innovation-variance identity `v q² h = s²(1-ρ²)`;
- the closed-form modal second moment and its affine OU recurrence;
- uniqueness, nonnegativity, and strict positivity after positive elapsed time;
- exact summation of modal second moments and the geometric-series formula;
- differentiation of the exact transition coefficient;
- differentiation of the logarithmic innovation factor, proving equation (65) on the positive core;
- the closed form for each mode's transition-mean Fisher-information contribution;
- exact finite-sum identities for variance, scale, and drift/scale cross-information.

These results formalize deterministic and analytic dependencies of Proposition 9.14, Theorem 9.11, Lemma 9.5, and Lemma 9.7. They do not establish the mixed-information limit or score CLT: those still require uniform small-mesh estimates, normalized modal summation bounds, and probability limit theory.

## Corrected consistency: deterministic argmin layer

**Lean file:** `RequestProject/ArgminConsistency.lean`.

The deterministic consistency logic required after KL separation and stochastic uniform control is now proved. The development defines uniform criterion error and nonvacuous deterministic separation, and proves:

- every exact minimizer lies in the separated good set when the gap exceeds twice the uniform error;
- the metric-ball specialization;
- simultaneous drift and scale coordinate bounds from the two separation inequalities corresponding to (91) and (92);
- conversion of coordinatewise bounds to product distance;
- sequential convergence of exact minimizers from eventual separation at every radius and eventual domination of uniform errors.

The theorem does not assume consistency or encode the conclusion as a premise. Its remaining inputs correspond exactly to the unresolved mathematical burden in the paper: full Lemma 9.7 and uniform stochastic criterion control at the required rates. Thus corrected Theorem 9.13 is now reduced to those explicit dependencies, while condition (95) remains required wherever used to prove the stochastic error domination.

## Quantitative small-mesh and drift-separation layer

**Lean file:** `RequestProject/OUSmallMesh.lean`.

The following explicit inequalities are now proved:

- `1 - exp(-x) ≤ x` and `x/(1+x) ≤ 1-exp(-x)`;
- the resolved-mesh bound `x/2 ≤ 1-exp(-x)` on `[0,1]`;
- two-sided comparison `Δ/2 ≤ h(θ,λ,Δ) ≤ Δ` under `2 θ λ Δ ≤ 1`;
- the corresponding two-sided exact modal innovation-variance bound;
- positivity and upper bound one for the exact transition coefficient;
- a uniform lower bound on transition coefficients from a mesh bound;
- a quantitative lower bound for exact transition-coefficient differences under drift separation;
- its squared form and the resulting pointwise lower bound for the transition-mean term in Gaussian KL.

This replaces several informal uses of Taylor expansion and the mean value theorem in Lemmas 9.4 and 9.7 by kernel-checked inequalities with explicit hypotheses. Summing these pointwise estimates into the full order-`Λ_N` drift-separation theorem still requires a formal high-mode counting argument and summed modal second-moment lower bound.

## Spectral high-mode summation layer

**Lean file:** `RequestProject/SpectralSummation.lean`.

The fixed-spectrum partial-sum infrastructure needed by Lemma 9.7 is now formalized:

- exact prefix/tail decomposition of `Λ_N`;
- monotonicity for nonnegative spectra;
- eventual domination of every fixed prefix by half of a divergent partial sum;
- eventual lower bound of the high-mode tail by `Λ_N/2`;
- summation of pointwise modal lower bounds into an order-`Λ_N` bound, both for an explicit tail and for a full nonnegative modal sum.

During formalization, the full-sum theorem was found to be false without nonnegativity of the modal contributions: a fixed negative low mode survives when the proportionality constant is zero. The corrected theorem includes the necessary nonnegativity hypothesis, and `low_mode_nonnegativity_is_necessary` gives a Lean-verified counterexample to the omitted-hypothesis version. For the paper's KL application this added premise is available because every modal KL contribution is nonnegative.

## Modal burn-in and KL drift lower bound

**Lean files:** `RequestProject/ModalBurnIn.lean` and `RequestProject/ModalKLSeparation.lean`.

The modal second-moment step in the drift portion of Lemma 9.7 is now formalized with explicit finite-sample hypotheses:

- squared exact transition powers are antitone in observation time;
- after any burn-in index where the squared transition coefficient is at most one half, each later second moment is at least half the stationary variance;
- the exact number of post-burn-in observations and their summed second-moment lower bound;
- the `n/4` stationary-variance lower bound when burn-in uses at most half the sample;
- domination of the post-burn-in sum by the full nonnegative observation-time sum;
- exact factorization and nonnegativity of the modewise transition-mean KL contribution;
- a fully explicit order-`λ_k` modewise KL lower bound under drift separation, positive compact scale bounds, a burn-in decay condition, and `n Δ = T`.

Together with `SpectralSummation.lean`, this reduces the drift part of global KL separation to constructing burn-in indices uniformly for all sufficiently high modes and checking their decay and half-sample conditions. Those spectral/time-index conditions remain explicit rather than being hidden behind an asymptotic assertion.

## Explicit half-life burn-in construction

**Lean file:** `RequestProject/BurnInConstruction.lean`.

The burn-in index left abstract in the previous layer is now constructed as
`ceil(log 2 / (2 θ λ Δ))`. The following are machine checked:

- the real half-life lies below the selected integer index;
- the exact squared OU transition coefficient at that index is at most one half;
- the ceiling is less than one observation beyond the real half-life;
- an explicit sample-size inequality implies that twice the burn-in index is at most `n`;
- a horizon-based sufficient condition with `n Δ = T`;
- the full modal second-moment lower bound with the explicit half-life index;
- the modewise order-`λ_k` KL drift lower bound with all burn-in premises discharged.

The remaining global drift-separation assembly is now reduced to showing that the explicit sample-size inequality holds uniformly above a fixed spectral cutoff and combining the resulting modal bound with the verified spectral tail summation theorem.

## Global drift KL separation assembly

**Lean file:** `RequestProject/GlobalDriftSeparation.lean`.

The deterministic drift half of Lemma 9.7 is now assembled across a fixed spectrum:

- definition and nonnegativity of the global finite-modal transition-mean KL sum;
- replacement of the mode-dependent exponential factor by a common constant under a uniform `λ_k Δ` bound;
- a finite-stage high-mode-tail lower bound obtained by summing the explicit half-life modal estimates;
- an eventual order-`Λ_N` lower bound using divergence of the fixed spectral partial sums and the verified finite-prefix/tail theorem.

The final theorem keeps the two genuinely required uniform high-mode premises explicit: a common mesh bound and the half-life sample-size inequality. It proves the exact order-`Λ_N` conclusion rather than assuming global separation. This completes the deterministic drift-separation chain; full paper Lemma 9.7 still also requires the scale-separation half uniformly over the compact drift interval.

## Global scale KL separation core

**Lean file:** `RequestProject/GlobalScaleSeparation.lean`.

The scale half of Lemma 9.7 is now formalized at the finite-dimensional analytic level:

- exact factorization of the Gaussian variance ratio into scale and innovation-factor ratios;
- a quantitative perturbation lemma showing that a scale ratio separated from one remains separated after a uniformly small multiplicative factor perturbation;
- specialization to exact OU variance ratios;
- definition and exact repetition identity for the global `ψ` contrast across all mode-time cells;
- compact-uniform positivity of `ψ` converted into an order-`Nn` lower bound;
- direct pointwise-to-global summation and a uniform OU scale-ratio separation theorem.

## Explicit compact scale-ratio bounds

**Lean file:** `RequestProject/ScaleRatioBounds.lean`.

The two analytic inputs left open in the preceding scale-separation core are now machine checked:

- the normalized exact innovation factor differs from one by at most `2 θ λ Δ`;
- uniformly over a compact positive drift interval, the ratio `h(θ₀,λ,Δ)/h(θ,λ,Δ)` differs from one by at most `8 θUpper λ Δ` under the resolved-mesh condition;
- separation of positive variance scales on a compact interval yields both an explicit scale-ratio gap and an upper bound for that ratio;
- if the exact-factor perturbation is at most half of the scale-ratio gap, the full exact OU variance ratio remains separated from one by the other half.

This discharges the finite-dimensional compact-uniform perturbation step identified at the end of the preceding section. Completing paper Lemma 9.7 still requires the asymptotic assembly: derive the stated perturbation inequality uniformly from the paper's mesh regime, split the complement of the parameter ball into drift- and scale-separated regions, and combine this scale bound with the already verified global drift bound and stochastic criterion control.
