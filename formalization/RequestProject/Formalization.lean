import Mathlib

/-!
# Formalisation of foundational arguments in `paper_merged.pdf`

This file begins a machine-checked formalisation of the paper.  It focuses on the
set-theoretic identification arguments, the exact scalar spectral recovery
formulas, the operator--forcing gauge calculation, and the cross-world variance
identity.  Analytic and probabilistic results requiring a full SPDE and
asymptotic-statistics development are not silently represented by assumptions.
-/

namespace OperatorInterventions

section Identification

variable {Parameter Observation Target : Type*}

/-- Definition 9.3: a target is identified when it is constant on every
observational fibre. -/
def Identified (obs : Parameter → Observation) (target : Parameter → Target) : Prop :=
  ∀ ⦃p₁ p₂⦄, obs p₁ = obs p₂ → target p₁ = target p₂

/-
The fibre criterion (Lemma 4.1 / Theorem 9.5), in its direct form.
-/
theorem identified_iff_constant_on_fibres
    (obs : Parameter → Observation) (target : Parameter → Target) :
    Identified obs target ↔ ∀ ⦃p₁ p₂⦄, obs p₁ = obs p₂ → target p₁ = target p₂ := by
  rfl

/-
The nontrivial “choose a representative of each fibre” formulation of the
fibre criterion.  Identification is equivalent to the target descending to the
range of the observation map.
-/
theorem identified_iff_factors_through_range
    (obs : Parameter → Observation) (target : Parameter → Target) :
    Identified obs target ↔
      ∃ descended : Set.range obs → Target,
        ∀ p, descended ⟨obs p, ⟨p, rfl⟩⟩ = target p := by
  constructor;
  · intro h
    use fun ⟨y, hy⟩ => target (Classical.choose hy);
    exact fun p => h ( Classical.choose_spec ( ⟨ p, rfl ⟩ : ∃ p', obs p' = obs p ) );
  · rintro ⟨ descended, hdescended ⟩ p₁ p₂ h; have := hdescended p₁; have := hdescended p₂; aesop;

/-
If an observation map is injective, every target is identified.
-/
theorem identified_of_injective
    (obs : Parameter → Observation) (target : Parameter → Target)
    (hobs : Function.Injective obs) : Identified obs target := by
  intro p₁ p₂ h; have := @hobs p₁ p₂; aesop;

/-
A target transported through an identified invariant module is identified.
-/
theorem identified_comp
    (obs : Parameter → Observation) (invariant : Parameter → Target)
    {Result : Type*} (transport : Target → Result)
    (h : Identified obs invariant) : Identified obs (transport ∘ invariant) := by
  exact fun p₁ p₂ hp => congr_arg transport ( h hp )

/-
Known additive-error deconvolution is cancellation in the
characteristic-function identity.  This is Proposition 9.12 stripped to the
only algebraic step used in its proof.
-/
theorem deconvolution_unique
    {Index : Type*} (error observed latent₁ latent₂ : Index → ℂ)
    (herror : ∀ t, error t ≠ 0)
    (h₁ : ∀ t, observed t = latent₁ t * error t)
    (h₂ : ∀ t, observed t = latent₂ t * error t) :
    latent₁ = latent₂ := by
  grind +qlia

end Identification

section SpectralRecovery

noncomputable section

/-- The exact scalar spectral transition coefficient, equation (36). -/
def spectralRho (theta lambda delta : ℝ) : ℝ :=
  Real.exp (-theta * lambda * delta)

/-- Recovery formula displayed in Theorem 4.1. -/
def thetaFromRho (rho lambda delta : ℝ) : ℝ :=
  -Real.log rho / (lambda * delta)

/-
The recovery formula really is a left inverse on the positive spectral core.
-/
theorem thetaFromRho_spectralRho
    {theta lambda delta : ℝ} (hlambda : 0 < lambda) (hdelta : 0 < delta) :
    thetaFromRho (spectralRho theta lambda delta) lambda delta = theta := by
  unfold thetaFromRho spectralRho
  rw [Real.log_exp]
  field_simp

/-
Positivity and reality rule out aliasing for a scalar spectral mode.
-/
theorem spectralRho_injective
    {lambda delta : ℝ} (hlambda : 0 < lambda) (hdelta : 0 < delta) :
    Function.Injective (fun theta : ℝ => spectralRho theta lambda delta) := by
  intro theta₁ theta₂ h
  apply (mul_left_cancel₀ (ne_of_gt hlambda) :
    lambda * theta₁ = lambda * theta₂ → theta₁ = theta₂)
  apply (mul_left_cancel₀ (ne_of_gt hdelta) :
    delta * (lambda * theta₁) = delta * (lambda * theta₂) → _)
  have hexp := Real.exp_injective h
  unfold spectralRho at hexp
  linarith

/-- Innovation variance factor, equation (37), with the removable boundary
case filled continuously. -/
def spectralH (theta lambda delta : ℝ) : ℝ :=
  if theta * lambda = 0 then delta
  else (1 - Real.exp (-2 * theta * lambda * delta)) / (2 * theta * lambda)

/-
On the positive core the innovation variance factor is strictly positive.
-/
theorem spectralH_pos
    {theta lambda delta : ℝ} (htheta : 0 < theta)
    (hlambda : 0 < lambda) (hdelta : 0 < delta) :
    0 < spectralH theta lambda delta := by
  unfold spectralH; split_ifs <;> first | positivity | exact div_pos ( by linarith [ Real.exp_lt_one_iff.2 ( show -2 * theta * lambda * delta < 0 by nlinarith [ mul_pos htheta hlambda ] ) ] ) ( by nlinarith [ mul_pos htheta hlambda ] ) ;

/-- Algebraic recovery of the positive scale from a known variance factor. -/
def sigmaFromVariance (variance q h : ℝ) : ℝ :=
  Real.sqrt (variance / (q ^ 2 * h))

/-
If `variance = sigma² q² h` on the positive core, the displayed recovery
formula returns `sigma`.
-/
theorem sigmaFromVariance_exact
    {sigma q h : ℝ} (hsigma : 0 ≤ sigma) (hq : q ≠ 0) (hh : 0 < h) :
    sigmaFromVariance (sigma ^ 2 * q ^ 2 * h) q h = sigma := by
  unfold sigmaFromVariance;
  rw [ mul_assoc, mul_div_cancel_right₀ _ ( by positivity ), Real.sqrt_sq hsigma ]

/-
The covariance-ratio step in Theorem 4.1, isolated from probability theory:
if `covariance = rho * variance` and variance is nonzero, its ratio recovers rho.
-/
theorem covariance_ratio_recovers_rho
    {covariance rho variance : ℝ} (hvariance : variance ≠ 0)
    (hcov : covariance = rho * variance) :
    covariance / variance = rho := by
  grind +revert

/-
A compact formal version of the three-time identification calculation:
the transition summary consisting of `rho` and the innovation variance uniquely
identifies positive `(theta, sigma)` when `q ≠ 0`.
-/
theorem exactTransitionSummary_injective
    {lambda delta q : ℝ} (hlambda : 0 < lambda) (hdelta : 0 < delta) (hq : q ≠ 0) :
    Function.Injective (fun p : {x : ℝ × ℝ // 0 < x.1 ∧ 0 < x.2} =>
      (spectralRho p.1.1 lambda delta,
        p.1.2 ^ 2 * q ^ 2 * spectralH p.1.1 lambda delta)) := by
  intro p₁ p₂ h_eq;
  -- From the equality of the first components, we get that $p₁.1 = p₂.1$.
  have h_theta : p₁.val.1 = p₂.val.1 := by
    apply spectralRho_injective hlambda hdelta;
    injection h_eq;
  simp_all +decide [ Prod.ext_iff ];
  exact Subtype.ext <| Prod.ext h_theta <| by nlinarith [ h_eq.resolve_right <| ne_of_gt <| OperatorInterventions.spectralH_pos ( show 0 < ( p₂ : ℝ × ℝ ).1 from p₂.2.1 ) hlambda hdelta, p₁.2.2, p₂.2.2 ] ;

end

end SpectralRecovery

section ProfileLikelihoodAudit

noncomputable section

/-- Twice the negative Gaussian log-likelihood for one residual block, up to an
additive constant, parameterised by scale variance `v`, transition factor `h`,
and squared residual `r`. -/
def gaussianProfileObjective (v h r : ℝ) : ℝ :=
  Real.log (v * h) + r / (v * h)

/-
A machine-checked counterexample to the finite-sample profiling instruction
in Proposition 9.13.  Unconstrained profiling favours candidate A, but after the
scale constraint `v ≥ 1` is imposed, candidate B has the smaller objective.
Thus selecting theta with the unconstrained profile and merely projecting its
scale afterwards need not produce the constrained joint MLE.
-/
theorem projecting_scale_after_unconstrained_profile_can_fail :
    let hA := Real.exp 5
    let rA := (1 : ℝ) / 10
    let hB := (1 : ℝ)
    let rB := (1 : ℝ)
    let vA := rA / hA
    let vB := rB / hB
    gaussianProfileObjective vA hA rA < gaussianProfileObjective vB hB rB ∧
      gaussianProfileObjective 1 hB rB < gaussianProfileObjective 1 hA rA := by
  norm_num [ gaussianProfileObjective ];
  exact ⟨ Real.log_neg ( by norm_num ) ( by norm_num ), lt_add_of_lt_of_nonneg ( by norm_num ) ( by positivity ) ⟩

end

end ProfileLikelihoodAudit

section Gauge

variable {H : Type*} [AddCommGroup H]

/-
The factual operator--forcing gauge identity of Theorem 8.1 / 9.45.
-/
theorem operator_forcing_gauge
    (A L : H →+ H) (G : H → H) (u : H) :
    (A - L) u + (G u + L u) = A u + G u := by
  simp

/-
After replacing both operator modules by the same intervention operator,
the transformed forcing module leaves precisely the extra `L u` term.
-/
theorem gauge_after_common_intervention
    (intervened L : H →+ H) (G : H → H) (u : H) :
    intervened u + (G u + L u) = (intervened u + G u) + L u := by
  grind

end Gauge

section CrossWorld

/-
Algebra behind the cross-world variance formula in Section 8.
-/
theorem variance_of_difference_identity
    {varianceA varianceB covariance : ℝ}
    {meanA meanB secondA secondB cross : ℝ}
    (hA : varianceA = secondA - meanA ^ 2)
    (hB : varianceB = secondB - meanB ^ 2)
    (hcov : covariance = cross - meanA * meanB) :
    (secondA + secondB - 2 * cross) - (meanA - meanB) ^ 2 =
      varianceA + varianceB - 2 * covariance := by
  linarith

/-
Substituting covariance `rho * sqrt(va) * sqrt(vb)` yields the paper's
cross-world variance display.
-/
theorem variance_contrast_with_correlation
    (varianceA varianceB rho : ℝ) :
    varianceA + varianceB - 2 * (rho * Real.sqrt varianceA * Real.sqrt varianceB) =
      varianceA + varianceB - 2 * rho * Real.sqrt varianceA * Real.sqrt varianceB := by
  ring

end CrossWorld

end OperatorInterventions