import RequestProject.Formalization

/-!
# Corrected constrained profiling and the missing growth hypothesis

This file replaces the invalid “profile without constraints, then project once”
construction by the logically correct pointwise constrained profile.  The
order-theoretic theorem is independent of regularity or existence assumptions:
once a constrained scale minimizer has been selected for every drift parameter,
minimizing that constrained profile is exactly joint minimization.

It also isolates condition (95) from Theorem 9.13.  The final theorem gives an
explicit asymptotic countermodel showing that divergence of `Λ`, together with
`λ / Λ → 0`, does not by itself imply `sqrt N * λ / Λ → 0`.  Thus (95), or a
hypothesis such as Weyl growth from which it follows, must be added to the
consistency theorem.
-/

namespace OperatorInterventions

section CorrectedConstrainedProfile

variable {Theta Scale : Type*}

/-- `v` minimizes `objective theta ·` over the admissible scale set. -/
def IsConstrainedScaleMin
    (objective : Theta → Scale → ℝ) (admissibleScale : Set Scale)
    (theta : Theta) (v : Scale) : Prop :=
  v ∈ admissibleScale ∧ ∀ w ∈ admissibleScale, objective theta v ≤ objective theta w

/-- Corrected constrained profiling: a scale optimizer must be selected at
*every* candidate drift value before the drift profile is minimized. -/
def IsCorrectedProfileMLE
    (objective : Theta → Scale → ℝ)
    (admissibleTheta : Set Theta) (admissibleScale : Set Scale)
    (scaleAt : Theta → Scale) (thetaHat : Theta) : Prop :=
  thetaHat ∈ admissibleTheta ∧
  (∀ theta ∈ admissibleTheta,
    IsConstrainedScaleMin objective admissibleScale theta (scaleAt theta)) ∧
  ∀ theta ∈ admissibleTheta,
    objective thetaHat (scaleAt thetaHat) ≤ objective theta (scaleAt theta)

/-
The corrected pointwise constrained profile produces a genuine joint MLE.
-/
theorem corrected_profile_is_joint_min
    {objective : Theta → Scale → ℝ}
    {admissibleTheta : Set Theta} {admissibleScale : Set Scale}
    {scaleAt : Theta → Scale} {thetaHat : Theta}
    (h : IsCorrectedProfileMLE objective admissibleTheta admissibleScale
      scaleAt thetaHat) :
    thetaHat ∈ admissibleTheta ∧ scaleAt thetaHat ∈ admissibleScale ∧
      ∀ theta ∈ admissibleTheta, ∀ v ∈ admissibleScale,
        objective thetaHat (scaleAt thetaHat) ≤ objective theta v := by
  obtain ⟨ htheta, hscale, hprofile ⟩ := h;
  exact ⟨ htheta, hscale thetaHat htheta |>.1, fun theta htheta v hv => le_trans ( hprofile theta htheta ) ( hscale theta htheta |>.2 v hv ) ⟩

/-
Conversely, every joint constrained minimizer minimizes its own scale
section and the profile induced by any pointwise constrained scale selection.
-/
theorem joint_min_is_corrected_profile
    {objective : Theta → Scale → ℝ}
    {admissibleTheta : Set Theta} {admissibleScale : Set Scale}
    {scaleAt : Theta → Scale} {thetaHat : Theta} {vHat : Scale}
    (hTheta : thetaHat ∈ admissibleTheta)
    (hJoint : ∀ theta ∈ admissibleTheta, ∀ v ∈ admissibleScale,
      objective thetaHat vHat ≤ objective theta v)
    (hSelections : ∀ theta ∈ admissibleTheta,
      IsConstrainedScaleMin objective admissibleScale theta (scaleAt theta))
    (hAt : scaleAt thetaHat = vHat) :
    IsCorrectedProfileMLE objective admissibleTheta admissibleScale
      scaleAt thetaHat := by
  grind +locals

/-
For one Gaussian residual block, the pointwise constrained scale optimizer
is the unconstrained optimizer clamped to the scale interval.  Crucially, this
clamping is performed separately for each drift candidate (whose `h` and `r`
change), rather than once after choosing an unconstrained drift optimizer.
-/
theorem gaussian_profile_pointwise_clamp
    {lower upper h r : ℝ}
    (hlower : 0 < lower) (hlu : lower ≤ upper)
    (hh : 0 < h) (hr : 0 < r) :
    let unconstrained := r / h
    let constrained := max lower (min upper unconstrained)
    constrained ∈ Set.Icc lower upper ∧
      ∀ v ∈ Set.Icc lower upper,
        gaussianProfileObjective constrained h r ≤
          gaussianProfileObjective v h r := by
  refine' ⟨ ⟨ le_max_left _ _, max_le hlu ( min_le_left _ _ ) ⟩, _ ⟩;
  intro v hv
  simp [gaussianProfileObjective];
  -- Let $x = r / h$. We need to show that $f(v) = \log v + x / v$ is minimized at $v = \max(\min(x, upper), lower)$.
  set x := r / h
  have hf : ∀ v ∈ Set.Icc lower upper, Real.log v + x / v ≥ Real.log (max lower (min upper x)) + x / (max lower (min upper x)) := by
    cases le_total x lower <;> cases le_total x upper <;> simp +decide [ * ];
    · intro v hv₁ hv₂; rw [ add_div', add_div' ] <;> try linarith;
      have h_log : Real.log v ≥ Real.log lower + (v - lower) / v := by
        have := Real.log_le_sub_one_of_pos ( show 0 < lower / v by exact div_pos hlower ( by linarith ) );
        rw [ Real.log_div ] at this <;> ring_nf at * <;> nlinarith [ inv_mul_cancel₀ ( by linarith : v ≠ 0 ) ];
      simp +zetaDelta at *;
      field_simp at *;
      rw [ add_div', div_le_iff₀ ] at h_log <;> nlinarith [ mul_div_cancel₀ r ( by linarith : v ≠ 0 ) ];
    · grind;
    · intro v hv₁ hv₂; rw [ div_self <| ne_of_gt <| div_pos hr hh ] ;
      have := Real.log_le_sub_one_of_pos ( show 0 < x / v by exact div_pos ( div_pos hr hh ) ( by linarith ) );
      rw [ Real.log_div ] at this <;> linarith [ show 0 < x by positivity, show 0 < v by linarith ];
    · -- Let's choose any $v$ in the interval $[lower, upper]$.
      intro v hv_lower hv_upper
      have h_deriv_neg : ∀ v ∈ Set.Ioo lower upper, deriv (fun v => Real.log v + x / v) v ≤ 0 := by
        intro v hv; norm_num [ div_eq_mul_inv, differentiableAt_inv, show v ≠ 0 by linarith [ hv.1 ] ];
        rw [ ← div_eq_mul_inv, inv_eq_one_div, div_le_div_iff₀ ] <;> nlinarith [ hv.1, hv.2 ];
      by_contra h_contra;
      have := exists_deriv_eq_slope ( f := fun v => Real.log v + x / v ) ( show v < upper from lt_of_le_of_ne hv_upper ( by rintro rfl; linarith ) ) ; norm_num at *;
      contrapose! this;
      exact ⟨ continuousOn_of_forall_continuousAt fun y hy => by exact ContinuousAt.add ( Real.continuousAt_log ( by linarith [ hy.1 ] ) ) ( ContinuousAt.div continuousAt_const continuousAt_id ( by linarith [ hy.1 ] ) ), fun y hy => DifferentiableAt.differentiableWithinAt ( by exact DifferentiableAt.add ( Real.differentiableAt_log ( by linarith [ hy.1 ] ) ) ( DifferentiableAt.div ( differentiableAt_const _ ) differentiableAt_id ( by linarith [ hy.1 ] ) ) ), fun c hc => by rw [ ne_eq, eq_div_iff ] <;> nlinarith [ h_deriv_neg c ( by linarith ) ( by linarith ) ] ⟩;
  rw [ Real.log_mul, Real.log_mul ] <;> try linarith [ hv.1, hv.2 ];
  · convert add_le_add_right ( hf v hv ) ( Real.log h ) using 1 <;> ring;
  · exact ne_of_gt ( lt_max_of_lt_left hlower )

/-
The clamping formula also covers the degenerate zero-residual case.
-/
theorem gaussian_profile_pointwise_clamp_nonneg
    {lower upper h r : ℝ}
    (hlower : 0 < lower) (hlu : lower ≤ upper)
    (hh : 0 < h) (hr : 0 ≤ r) :
    let unconstrained := r / h
    let constrained := max lower (min upper unconstrained)
    constrained ∈ Set.Icc lower upper ∧
      ∀ v ∈ Set.Icc lower upper,
        gaussianProfileObjective constrained h r ≤
          gaussianProfileObjective v h r := by
  by_cases hr_zero : r = 0;
  · simp_all +decide [ gaussianProfileObjective ];
    exact fun v hv₁ hv₂ => Real.log_le_log ( by cases max_cases lower ( Min.min upper 0 ) <;> cases min_cases upper 0 <;> nlinarith ) ( by cases max_cases lower ( Min.min upper 0 ) <;> cases min_cases upper 0 <;> nlinarith );
  · exact gaussian_profile_pointwise_clamp hlower hlu hh ( lt_of_le_of_ne hr ( Ne.symm hr_zero ) )

end CorrectedConstrainedProfile

section MissingGrowthHypothesis

/-- Aggregate information and largest-frequency sequences showing why the
no-dominant-coordinate part of Assumption 9.6 does not entail condition (95).
These values can also be realized at each stage by a triangular spectral array:
one coordinate has size `sqrt N` while the remaining mass is spread over the
other coordinates. -/
def aggregateCounterexample (n : ℕ) : ℝ := (n : ℝ) + 1

noncomputable def largestFrequencyCounterexample (n : ℕ) : ℝ :=
  Real.sqrt ((n : ℝ) + 1)

/-
As abstract rate conditions, `Λ_N → ∞` and `λ_N / Λ_N → 0` do not imply
`sqrt(N) * λ_N / Λ_N → 0`: for the displayed two sequences the strengthened
ratio is identically one.  This intentionally addresses only the implication
between the displayed rates; the audit separately records the spectral
partial-sum structure.
-/
theorem two_rate_conditions_do_not_imply_condition95 :
    Filter.Tendsto aggregateCounterexample Filter.atTop Filter.atTop ∧
    Filter.Tendsto
      (fun n => largestFrequencyCounterexample n / aggregateCounterexample n)
      Filter.atTop (nhds 0) ∧
    (∀ n : ℕ, Real.sqrt ((n : ℝ) + 1) * largestFrequencyCounterexample n /
      aggregateCounterexample n = 1) := by
  refine' ⟨ _, _, _ ⟩ <;> norm_num [ aggregateCounterexample, largestFrequencyCounterexample ];
  · exact Filter.tendsto_atTop_add_const_right _ _ tendsto_natCast_atTop_atTop;
  · simpa [ Real.sqrt_div_self ] using tendsto_inv_atTop_zero.sqrt.comp ( Filter.tendsto_atTop_add_const_right _ _ tendsto_natCast_atTop_atTop );
  · exact fun n => by rw [ Real.mul_self_sqrt ( by positivity ), div_self ( by positivity ) ] ;

end MissingGrowthHypothesis

end OperatorInterventions