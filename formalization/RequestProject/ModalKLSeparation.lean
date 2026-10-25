import RequestProject.ModalBurnIn

/-!
# Quantitative modal drift KL separation

This file combines exact transition separation, innovation-variance bounds, and
post-burn-in second moments into a single modewise lower bound.  It is the
finite-dimensional inequality that is summed over high modes in Lemma 9.7.
-/

namespace OperatorInterventions

noncomputable section

/-- Expected transition-mean contribution to twice the Gaussian KL contrast
for one mode, expressed through the exact true second moments. -/
def ouModeMeanKL2
    (theta0 v0 theta v q lambda delta u0 : ℝ) (n : ℕ) : ℝ :=
  ∑ j ∈ Finset.range n,
    ((ouRho theta lambda delta - ouRho theta0 lambda delta) ^ 2 *
      ouSecondMoment theta0 v0 q lambda delta u0 j) /
        (v * q ^ 2 * ouInnovationFactor theta lambda delta)

/-
Exact factorization of the modewise mean KL term.
-/
theorem ouModeMeanKL2_factorization
    (theta0 v0 theta v q lambda delta u0 : ℝ) (n : ℕ) :
    ouModeMeanKL2 theta0 v0 theta v q lambda delta u0 n =
      (ouRho theta lambda delta - ouRho theta0 lambda delta) ^ 2 /
          (v * q ^ 2 * ouInnovationFactor theta lambda delta) *
        (∑ j ∈ Finset.range n,
          ouSecondMoment theta0 v0 q lambda delta u0 j) := by
  rw [Finset.mul_sum _ _ _]
  simp +decide [ouModeMeanKL2]
  ring_nf
  exact Finset.sum_congr rfl fun _ _ => by ring

/-
Modewise order-`λ` drift separation after burn-in.  The assumption
`n * Δ = T` is retained explicitly rather than hidden in notation.
-/
theorem ouModeMeanKL2_lower_bound
    {theta0 v0 theta v vUpper q lambda delta u0 eps thetaUpper T : ℝ}
    {burn n : ℕ}
    (htheta0 : 0 < theta0) (htheta : 0 < theta)
    (htheta0Upper : theta0 ≤ thetaUpper) (hthetaUpper : theta ≤ thetaUpper)
    (hv0 : 0 < v0) (hv : 0 < v) (hvUpper : v ≤ vUpper)
    (hq : 0 < q) (hlambda : 0 < lambda) (hdelta : 0 < delta)
    (heps : 0 ≤ eps) (hsep : eps ≤ |theta - theta0|)
    (hburn : 2 * burn ≤ n)
    (hdecay : (ouRho theta0 lambda delta) ^ (2 * burn) ≤ 1 / 2)
    (horizon : (n : ℝ) * delta = T) :
    Real.exp (-2 * thetaUpper * lambda * delta) *
        v0 * T * eps ^ 2 / (16 * theta0 * vUpper) * lambda ≤
      ouModeMeanKL2 theta0 v0 theta v q lambda delta u0 n := by
  rw [ ouModeMeanKL2_factorization, div_mul_eq_mul_div ];
  -- Apply the lower bounds from `ouRho_difference_sq_lower_bound` and `full_sum_ouSecondMoment_lower_bound`.
  have h_lower_bounds :
    (ouRho theta lambda delta - ouRho theta0 lambda delta) ^ 2 ≥ (Real.exp (-thetaUpper * lambda * delta) * lambda * delta * eps) ^ 2 ∧
    (∑ j ∈ Finset.range n, ouSecondMoment theta0 v0 q lambda delta u0 j) ≥ (n : ℝ) * (v0 * q ^ 2 / (2 * theta0 * lambda)) / 4 := by
      apply And.intro;
      · apply ouRho_difference_sq_lower_bound hlambda hdelta.le htheta0Upper hthetaUpper heps hsep;
      · apply full_sum_ouSecondMoment_lower_bound;
        all_goals norm_cast; all_goals positivity;
  refine' le_trans _ ( mul_le_mul ( div_le_div_of_nonneg_right h_lower_bounds.1 _ ) h_lower_bounds.2 _ _ );
  · rw [ div_mul_eq_mul_div, div_le_div_iff₀ ];
    · rw [ ← horizon ] ; ring_nf;
      rw [ ← Real.exp_nat_mul ] ; ring_nf;
      field_simp;
      refine' le_trans ( mul_le_mul_of_nonneg_left ( ouInnovationFactor_le_delta htheta hlambda ) ( by positivity ) ) _;
      nlinarith [ show 0 ≤ ( n : ℝ ) * eps ^ 2 * delta by positivity ];
    · exact mul_pos ( mul_pos ( by norm_num ) htheta0 ) ( by linarith );
    · exact mul_pos ( mul_pos hv ( sq_pos_of_pos hq ) ) ( ouInnovationFactor_pos htheta hlambda hdelta );
  · exact mul_nonneg ( mul_nonneg hv.le ( sq_nonneg _ ) ) ( div_nonneg ( sub_nonneg.mpr ( Real.exp_le_one_iff.mpr ( by nlinarith [ mul_pos htheta hlambda ] ) ) ) ( by positivity ) );
  · positivity;
  · exact div_nonneg ( sq_nonneg _ ) ( mul_nonneg ( mul_nonneg hv.le ( sq_nonneg _ ) ) ( show 0 ≤ ouInnovationFactor theta lambda delta from by exact div_nonneg ( sub_nonneg.mpr <| Real.exp_le_one_iff.mpr <| by nlinarith [ mul_pos htheta hlambda ] ) <| by positivity ) )

/-
The preceding modal contribution is always nonnegative under positive
candidate variance and innovation factor.
-/
theorem ouModeMeanKL2_nonneg
    {theta0 v0 theta v q lambda delta u0 : ℝ} {n : ℕ}
    (htheta0 : 0 < theta0) (hv0 : 0 ≤ v0)
    (htheta : 0 < theta) (hv : 0 < v)
    (hlambda : 0 < lambda) (hdelta : 0 < delta) :
    0 ≤ ouModeMeanKL2 theta0 v0 theta v q lambda delta u0 n := by
  refine' Finset.sum_nonneg fun j hj => _;
  apply div_nonneg;
  · exact mul_nonneg ( sq_nonneg _ ) ( by exact ( by exact ( by exact ( by exact ( by exact ( by exact ( by exact by simpa using ( OperatorInterventions.ouSecondMoment_nonneg htheta0 hv0 hlambda hdelta.le j ) ) ) ) ) ) ) );
  · exact mul_nonneg ( mul_nonneg hv.le ( sq_nonneg q ) ) ( le_of_lt ( ouInnovationFactor_pos htheta hlambda hdelta ) )

end

end OperatorInterventions