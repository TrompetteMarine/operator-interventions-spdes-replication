import RequestProject.GlobalScaleSeparation

/-!
# Explicit uniform OU scale-ratio bounds

This file discharges the two elementary analytic inputs left explicit in the
scale half of global KL separation: exact innovation factors are uniformly
close to the mesh width, and separation of variance scales on a positive
compact interval gives separation of their ratios.
-/

namespace OperatorInterventions

noncomputable section

/-
The exact innovation factor, normalized by the mesh width, differs from
one by at most `2 θ λ Δ`.
-/
theorem ouInnovationFactor_normalized_close
    {theta lambda delta : ℝ}
    (htheta : 0 < theta) (hlambda : 0 < lambda) (hdelta : 0 < delta) :
    |ouInnovationFactor theta lambda delta / delta - 1| ≤
      2 * theta * lambda * delta := by
  unfold ouInnovationFactor;
  rw [ abs_le ];
  field_simp;
  constructor <;> nlinarith [ Real.exp_pos ( - ( 2 * theta * lambda * delta ) ), Real.exp_neg ( 2 * theta * lambda * delta ), mul_inv_cancel₀ ( ne_of_gt ( Real.exp_pos ( 2 * theta * lambda * delta ) ) ), Real.add_one_le_exp ( 2 * theta * lambda * delta ), Real.add_one_le_exp ( - ( 2 * theta * lambda * delta ) ), show 0 < 2 * theta * lambda * delta by positivity ]

/-
If both drift parameters lie below a common positive upper bound and the
mesh resolves that bound, the ratio of their exact innovation factors is
uniformly close to one.
-/
theorem ouInnovationFactor_ratio_close
    {theta0 theta lambda delta thetaUpper : ℝ}
    (htheta0 : 0 < theta0) (htheta : 0 < theta)
    (hlambda : 0 < lambda) (hdelta : 0 < delta)
    (htheta0Upper : theta0 ≤ thetaUpper)
    (hthetaUpper : theta ≤ thetaUpper)
    (hmesh : 2 * thetaUpper * lambda * delta ≤ 1) :
    |ouInnovationFactor theta0 lambda delta /
        ouInnovationFactor theta lambda delta - 1| ≤
      8 * thetaUpper * lambda * delta := by
  -- Let's simplify the expression inside the absolute value.
  set h0 := ouInnovationFactor theta0 lambda delta
  set h := ouInnovationFactor theta lambda delta
  have h0_pos : 0 < h0 := by
    exact OperatorInterventions.ouInnovationFactor_pos htheta0 hlambda hdelta
  have h_pos : 0 < h := by
    exact OperatorInterventions.ouInnovationFactor_pos htheta hlambda hdelta
  have h0_le : h0 ≤ delta := by
    apply ouInnovationFactor_le_delta; assumption; assumption
  have h_le : h ≤ delta := by
    exact OperatorInterventions.ouInnovationFactor_le_delta htheta hlambda
  have h0_ge : h0 ≥ delta / 2 := by
    apply half_delta_le_ouInnovationFactor htheta0 hlambda hdelta.le (by
    nlinarith [ mul_pos hlambda hdelta ])
  have h_ge : h ≥ delta / 2 := by
    apply half_delta_le_ouInnovationFactor htheta hlambda hdelta.le (by
    nlinarith [ mul_pos hlambda hdelta ]);
  rw [ div_sub_one, abs_div ] <;> try positivity;
  rw [ div_le_iff₀ ( abs_pos.mpr h_pos.ne' ) ];
  have h_abs : |h0 / delta - 1| ≤ 2 * thetaUpper * lambda * delta ∧ |h / delta - 1| ≤ 2 * thetaUpper * lambda * delta := by
    have h_abs : |h0 / delta - 1| ≤ 2 * theta0 * lambda * delta ∧ |h / delta - 1| ≤ 2 * theta * lambda * delta := by
      exact ⟨ by simpa using ouInnovationFactor_normalized_close htheta0 hlambda hdelta, by simpa using ouInnovationFactor_normalized_close htheta hlambda hdelta ⟩;
    exact ⟨ h_abs.1.trans ( by gcongr ), h_abs.2.trans ( by gcongr ) ⟩;
  rw [ abs_le ] at *;
  constructor <;> cases abs_cases h <;> nlinarith [ mul_div_cancel₀ h0 hdelta.ne', mul_div_cancel₀ h hdelta.ne', abs_le.mp h_abs.2 ]

/-
Separation of two positive variance scales on a compact interval implies
separation of their multiplicative ratio.
-/
theorem compact_scale_ratio_separated
    {v0 v lower upper eps : ℝ}
    (hlower : 0 < lower) (hv0Lower : lower ≤ v0) (hv0Upper : v0 ≤ upper)
    (hvLower : lower ≤ v) (hvUpper : v ≤ upper)
    (hsep : eps ≤ |v - v0|) :
    eps / upper ≤ |v0 / v - 1| ∧ v0 / v ≤ upper / lower := by
  constructor;
  · rw [ div_le_iff₀ ];
    · cases abs_cases ( v - v0 ) <;> cases abs_cases ( v0 / v - 1 ) <;> nlinarith [ mul_div_cancel₀ v0 ( by linarith : v ≠ 0 ) ];
    · linarith;
  · gcongr ; linarith [ div_nonneg hlower.le hlower.le ]

/-- A compactly separated scale remains uniformly separated after the exact
OU innovation-factor perturbation, under an explicit mesh condition. -/
theorem exact_ou_variance_ratio_separated
    {theta0 theta lambda delta thetaUpper v0 v lower upper eps : ℝ}
    (htheta0 : 0 < theta0) (htheta : 0 < theta)
    (hlambda : 0 < lambda) (hdelta : 0 < delta)
    (htheta0Upper : theta0 ≤ thetaUpper)
    (hthetaUpper : theta ≤ thetaUpper)
    (hlower : 0 < lower) (hv0Lower : lower ≤ v0) (hv0Upper : v0 ≤ upper)
    (hvLower : lower ≤ v) (hvUpper : v ≤ upper)
    (hscaleSep : eps ≤ |v - v0|)
    (hmesh : 2 * thetaUpper * lambda * delta ≤ 1)
    (hperturb : (upper / lower) * (8 * thetaUpper * lambda * delta) ≤
      eps / (2 * upper)) :
    eps / (2 * upper) ≤
      |(v0 * ouInnovationFactor theta0 lambda delta) /
          (v * ouInnovationFactor theta lambda delta) - 1| := by
  have h_compact : eps / upper ≤ |v0 / v - 1| ∧ v0 / v ≤ upper / lower := by
    apply compact_scale_ratio_separated hlower hv0Lower hv0Upper hvLower hvUpper hscaleSep;
  have h_perturb : |ouInnovationFactor theta0 lambda delta / ouInnovationFactor theta lambda delta - 1| ≤ 8 * thetaUpper * lambda * delta := by
    apply_rules [ ouInnovationFactor_ratio_close ];
  have h_combined : |v0 / v * (ouInnovationFactor theta0 lambda delta / ouInnovationFactor theta lambda delta) - 1| ≥ |v0 / v - 1| - v0 / v * |ouInnovationFactor theta0 lambda delta / ouInnovationFactor theta lambda delta - 1| := by
    have h_combined : |v0 / v * (ouInnovationFactor theta0 lambda delta / ouInnovationFactor theta lambda delta) - 1| ≥ |v0 / v - 1| - |v0 / v * (ouInnovationFactor theta0 lambda delta / ouInnovationFactor theta lambda delta - 1)| := by
      cases abs_cases ( v0 / v - 1 ) <;> cases abs_cases ( v0 / v * ( ouInnovationFactor theta0 lambda delta / ouInnovationFactor theta lambda delta - 1 ) ) <;> cases abs_cases ( v0 / v * ( ouInnovationFactor theta0 lambda delta / ouInnovationFactor theta lambda delta ) - 1 ) <;> linarith;
    exact h_combined.trans' ( by rw [ abs_mul, abs_of_nonneg ( show 0 ≤ v0 / v by exact div_nonneg ( by linarith ) ( by linarith ) ) ] );
  convert h_combined.trans' _ using 1;
  · rw [ div_mul_div_comm ];
  · refine le_trans ?_ ( sub_le_sub h_compact.1 ( mul_le_mul h_compact.2 h_perturb ?_ ?_ ) );
    · convert sub_le_sub_left hperturb ( eps / upper ) using 1 ; ring;
    · positivity;
    · exact div_nonneg ( by linarith ) ( by linarith )

end

end OperatorInterventions