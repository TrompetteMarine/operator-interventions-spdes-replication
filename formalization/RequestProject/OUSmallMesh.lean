import RequestProject.ArgminConsistency

/-!
# Quantitative exact OU small-mesh bounds

This file begins the uniform analytic estimates used in Lemma 9.4 and Lemma
9.7.  The bounds are explicit inequalities, rather than unexpanded `O(·)`
notation.
-/

namespace OperatorInterventions

noncomputable section

/-
Elementary upper bound for the exact exponential increment.
-/
theorem one_sub_exp_neg_le
    (x : ℝ) :
    1 - Real.exp (-x) ≤ x := by
  linarith [ Real.add_one_le_exp ( -x ) ]

/-
A global lower bound that is quantitative near zero.
-/
theorem div_one_add_le_one_sub_exp_neg
    {x : ℝ} (hx : 0 ≤ x) :
    x / (1 + x) ≤ 1 - Real.exp (-x) := by
  rw [ div_le_iff₀ ] <;> nlinarith [ Real.exp_pos ( -x ), Real.exp_neg x, mul_inv_cancel₀ ( ne_of_gt ( Real.exp_pos x ) ), Real.add_one_le_exp x, Real.add_one_le_exp ( -x ) ]

/-
On `[0,1]`, the exponential increment is bounded below by `x/2`.
-/
theorem half_mul_le_one_sub_exp_neg
    {x : ℝ} (hx : 0 ≤ x) (hx1 : x ≤ 1) :
    x / 2 ≤ 1 - Real.exp (-x) := by
  exact le_trans ( by rw [ div_le_div_iff₀ ] <;> nlinarith ) ( div_one_add_le_one_sub_exp_neg hx )

/-
Exact OU innovation factors are at most the mesh width.
-/
theorem ouInnovationFactor_le_delta
    {theta lambda delta : ℝ}
    (htheta : 0 < theta) (hlambda : 0 < lambda) :
    ouInnovationFactor theta lambda delta ≤ delta := by
  unfold ouInnovationFactor;
  rw [ div_le_iff₀ ( by positivity ) ];
  linarith [ Real.add_one_le_exp ( -2 * theta * lambda * delta ) ]

/-
Under an explicit resolved-mesh condition, the exact innovation factor is
bounded below by half the mesh width.
-/
theorem half_delta_le_ouInnovationFactor
    {theta lambda delta : ℝ}
    (htheta : 0 < theta) (hlambda : 0 < lambda) (hdelta : 0 ≤ delta)
    (hmesh : 2 * theta * lambda * delta ≤ 1) :
    delta / 2 ≤ ouInnovationFactor theta lambda delta := by
  unfold ouInnovationFactor;
  convert div_le_div_of_nonneg_right ( half_mul_le_one_sub_exp_neg ( show 0 ≤ 2 * theta * lambda * delta by positivity ) ( by linarith ) ) ( show 0 ≤ 2 * theta * lambda by positivity ) using 1 <;> ring_nf
  norm_num [mul_assoc, mul_comm theta, mul_left_comm lambda,
    htheta.ne', hlambda.ne']

/-
Thus the exact modal innovation variance is uniformly comparable to
`v q² Δ` under the resolved-mesh condition.
-/
theorem ouTransitionVariance_two_sided
    {theta v q lambda delta : ℝ}
    (htheta : 0 < theta) (hv : 0 ≤ v) (hlambda : 0 < lambda)
    (hdelta : 0 ≤ delta) (hmesh : 2 * theta * lambda * delta ≤ 1) :
    v * q ^ 2 * (delta / 2) ≤
      v * q ^ 2 * ouInnovationFactor theta lambda delta ∧
      v * q ^ 2 * ouInnovationFactor theta lambda delta ≤
        v * q ^ 2 * delta := by
  constructor;
  · exact mul_le_mul_of_nonneg_left ( half_delta_le_ouInnovationFactor htheta hlambda hdelta hmesh ) ( by positivity );
  · exact mul_le_mul_of_nonneg_left (ouInnovationFactor_le_delta htheta hlambda) ( by positivity )

/-
The exact transition coefficient lies in `(0,1]` for nonnegative mesh.
-/
theorem ouRho_pos_le_one
    {theta lambda delta : ℝ}
    (htheta : 0 < theta) (hlambda : 0 < lambda) (hdelta : 0 ≤ delta) :
    0 < ouRho theta lambda delta ∧ ouRho theta lambda delta ≤ 1 := by
  exact ⟨ Real.exp_pos _, Real.exp_le_one_iff.mpr <| by nlinarith [ mul_pos htheta hlambda ] ⟩

/-
A resolved-mesh lower bound for the transition coefficient.
-/
theorem exp_neg_mesh_lower_bound
    {theta lambda delta bound : ℝ}
    (hbound : theta * lambda * delta ≤ bound) :
    Real.exp (-bound) ≤ ouRho theta lambda delta := by
  unfold ouRho; exact Real.exp_le_exp.mpr ( by linarith ) ;

/-
Quantitative drift separation for exact transition coefficients.  The
explicit common upper bound replaces the informal MVT intermediate point.
-/
theorem ouRho_difference_lower_bound
    {theta0 theta lambda delta thetaUpper : ℝ}
    (hlambda : 0 < lambda) (hdelta : 0 ≤ delta)
    (htheta0 : theta0 ≤ thetaUpper) (htheta : theta ≤ thetaUpper) :
    Real.exp (-thetaUpper * lambda * delta) * lambda * delta *
        |theta - theta0| ≤
      |ouRho theta lambda delta - ouRho theta0 lambda delta| := by
  by_cases h : theta = theta0;
  · aesop;
  · cases lt_or_gt_of_ne h <;> simp_all +decide [ abs_of_pos, mul_assoc ];
    · -- Using the mean value theorem on the exponential function, we get:
      have h_mean_value : ∃ c ∈ Set.Ioo theta theta0, Real.exp (-theta * lambda * delta) - Real.exp (-theta0 * lambda * delta) = (theta0 - theta) * lambda * delta * Real.exp (-c * lambda * delta) := by
        have := exists_deriv_eq_slope ( f := fun x => Real.exp ( -x * lambda * delta ) ) ‹_›;
        norm_num +zetaDelta at *;
        exact this ( Continuous.continuousOn <| by continuity ) ( Differentiable.differentiableOn <| by norm_num ) |> fun ⟨ c, hc₁, hc₂ ⟩ => ⟨ c, hc₁, by rw [ eq_div_iff ] at hc₂ <;> linarith ⟩;
      obtain ⟨ c, hc₁, hc₂ ⟩ := h_mean_value; simp_all +decide [ abs_of_neg, mul_assoc, mul_comm, mul_left_comm, ouRho ] ;
      rw [ abs_of_pos hlambda, abs_of_nonneg hdelta, abs_of_nonneg ( by linarith : 0 ≤ theta0 - theta ) ] ; exact mul_le_mul_of_nonneg_left ( mul_le_mul_of_nonneg_left ( mul_le_mul_of_nonneg_left ( Real.exp_le_exp.mpr <| by nlinarith [ mul_nonneg hlambda.le hdelta ] ) <| by linarith ) <| by linarith ) <| by linarith;
    · have h_mean_value : ∃ c ∈ Set.Ioo theta0 theta, deriv (fun t => Real.exp (-t * lambda * delta)) c = (Real.exp (-theta * lambda * delta) - Real.exp (-theta0 * lambda * delta)) / (theta - theta0) := by
        have := exists_deriv_eq_slope ( f := fun t => Real.exp ( -t * lambda * delta ) ) ‹_›;
        exact this ( Continuous.continuousOn <| by continuity ) ( Differentiable.differentiableOn <| by norm_num );
      obtain ⟨ c, hc₁, hc₂ ⟩ := h_mean_value; norm_num [ mul_assoc, mul_comm lambda ] at *;
      rw [ eq_div_iff ] at hc₂ <;> try linarith;
      unfold ouRho;
      ring_nf at *;
      cases abs_cases ( Real.exp ( - ( delta * lambda * theta ) ) - Real.exp ( - ( delta * lambda * theta0 ) ) ) <;> nlinarith [ show 0 ≤ delta * lambda * ( theta - theta0 ) by exact mul_nonneg ( mul_nonneg hdelta hlambda.le ) ( by linarith ), show Real.exp ( - ( delta * lambda * c ) ) ≥ Real.exp ( - ( thetaUpper * delta * lambda ) ) by exact Real.exp_le_exp.mpr ( by nlinarith [ mul_nonneg hdelta hlambda.le ] ) ]

/-
Squared quantitative drift separation, in the exact form used inside the
mean part of the Gaussian KL decomposition.
-/
theorem ouRho_difference_sq_lower_bound
    {theta0 theta lambda delta thetaUpper eps : ℝ}
    (hlambda : 0 < lambda) (hdelta : 0 ≤ delta)
    (htheta0 : theta0 ≤ thetaUpper) (htheta : theta ≤ thetaUpper)
    (heps : 0 ≤ eps) (hsep : eps ≤ |theta - theta0|) :
    (Real.exp (-thetaUpper * lambda * delta) * lambda * delta * eps) ^ 2 ≤
      (ouRho theta lambda delta - ouRho theta0 lambda delta) ^ 2 := by
  -- By the properties of the exponential function and the mean value theorem, we can bound the difference.
  have h_bound : abs (ouRho theta lambda delta - ouRho theta0 lambda delta) ≥ Real.exp (-thetaUpper * lambda * delta) * lambda * delta * abs (theta - theta0) := by
    apply_rules [ OperatorInterventions.ouRho_difference_lower_bound ];
  simpa [ sq_abs ] using pow_le_pow_left₀ ( by positivity ) ( le_trans ( mul_le_mul_of_nonneg_left hsep ( by positivity ) ) h_bound ) 2

/-
A pointwise modal lower bound for the transition-mean contribution to the
exact conditional KL contrast.
-/
theorem ou_mean_KL_term_lower_bound
    {theta0 theta lambda delta thetaUpper eps y variance : ℝ}
    (hlambda : 0 < lambda) (hdelta : 0 ≤ delta)
    (htheta0 : theta0 ≤ thetaUpper) (htheta : theta ≤ thetaUpper)
    (heps : 0 ≤ eps) (hsep : eps ≤ |theta - theta0|)
    (hvariance : 0 < variance) :
    (Real.exp (-thetaUpper * lambda * delta) * lambda * delta * eps) ^ 2 *
        y ^ 2 / variance ≤
      ((ouRho theta lambda delta - ouRho theta0 lambda delta) * y) ^ 2 /
        variance := by
  gcongr;
  convert mul_le_mul_of_nonneg_right ( ouRho_difference_sq_lower_bound hlambda hdelta htheta0 htheta heps hsep ) ( sq_nonneg y ) using 1 ; ring

end

end OperatorInterventions