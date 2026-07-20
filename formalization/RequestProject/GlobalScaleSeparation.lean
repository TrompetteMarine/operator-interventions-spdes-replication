import RequestProject.GlobalDriftSeparation

/-!
# Global Gaussian scale separation

This file formalizes the scale half of the KL-separation argument.  It isolates
how a separated scale ratio remains separated after a uniformly small
multiplicative perturbation from exact OU innovation factors, then sums the
resulting `ψ` contrast over every mode-time cell.
-/

namespace OperatorInterventions

noncomputable section

/-
The variance ratio decomposes into a scale ratio and an exact innovation-
factor ratio.
-/
theorem ou_variance_ratio_factorization
    (v0 v h0 h : ℝ) :
    (v0 * h0) / (v * h) = (v0 / v) * (h0 / h) := by
  rw [ div_mul_div_comm ]

/-
A multiplicative perturbation of a separated positive scale ratio remains
separated from one.
-/
theorem mul_ratio_separated_from_one
    {base ratio delta eta upper : ℝ}
    (hbase0 : 0 ≤ base) (hbaseUpper : base ≤ upper)
    (hsep : delta ≤ |base - 1|)
    (hratio : |ratio - 1| ≤ eta) :
    delta - upper * eta ≤ |base * ratio - 1| := by
  cases abs_cases ( base - 1 ) <;> cases abs_cases ( base * ratio - 1 ) <;> nlinarith [ abs_le.mp hratio ]

/-
Exact specialization to an OU variance ratio.
-/
theorem ou_variance_ratio_separated
    {v0 v h0 h delta eta upper : ℝ}
    (hv0 : 0 ≤ v0) (hv : 0 < v)
    (hbaseUpper : v0 / v ≤ upper)
    (hscaleSep : delta ≤ |v0 / v - 1|)
    (hfactorClose : |h0 / h - 1| ≤ eta) :
    delta - upper * eta ≤
      |(v0 * h0) / (v * h) - 1| := by
  rw [ou_variance_ratio_factorization]
  exact mul_ratio_separated_from_one (by positivity) hbaseUpper hscaleSep hfactorClose

/-- Finite Gaussian variance contrast, with one ratio for each mode and the
same ratio repeated over all observation times. -/
def globalVariancePsi
    (ratio : Fin N → ℝ) (n : ℕ) : ℝ :=
  ∑ k : Fin N, ∑ _j ∈ Finset.range n, gaussianPsi (ratio k)

/-
Exact repetition identity for the global variance contrast.
-/
theorem globalVariancePsi_eq
    (ratio : Fin N → ℝ) (n : ℕ) :
    globalVariancePsi ratio n =
      (n : ℝ) * ∑ k : Fin N, gaussianPsi (ratio k) := by
  unfold globalVariancePsi; norm_num [ Finset.mul_sum _ _ _, mul_comm ] ;

/-
Compact-uniform separation of every variance ratio implies an order-`Nn`
lower bound for the scale part of twice the Gaussian KL contrast.
-/
theorem globalVariancePsi_lower_bound
    (ratio : Fin N → ℝ) (n : ℕ)
    {a b eps : ℝ} (ha : 0 < a) (heps : 0 < eps)
    (hrange : ∀ k, ratio k ∈ Set.Icc a b)
    (hsep : ∀ k, eps ≤ |ratio k - 1|)
    (hN : 0 < N) :
    ∃ c > 0,
      c * ((N * n : ℕ) : ℝ) ≤ globalVariancePsi ratio n := by
  obtain ⟨c, hc_pos, hc_bound⟩ : ∃ c > 0, ∀ k, c ≤ gaussianPsi (ratio k) := by
    -- By GaussianPsi_uniform_separation, there exists a constant c > 0 such that for all ratio k in [a, b], c ≤ gaussianPsi (ratio k).
    obtain ⟨c, hc_pos, hc⟩ : ∃ c > 0, ∀ x ∈ Set.Icc a b, eps ≤ |x - 1| → c ≤ gaussianPsi x := by
      apply gaussianPsi_uniform_separation ha heps;
      exact ⟨ ratio ⟨ 0, hN ⟩, hrange _, hsep _ ⟩;
    exact ⟨ c, hc_pos, fun k => hc _ ( hrange k ) ( hsep k ) ⟩;
  refine' ⟨ c, hc_pos, _ ⟩;
  rw [ globalVariancePsi_eq ];
  simpa [ mul_comm, mul_assoc, mul_left_comm, Finset.mul_sum _ _ _ ] using mul_le_mul_of_nonneg_left ( Finset.sum_le_sum fun i ( hi : i ∈ Finset.univ ) => hc_bound i ) ( Nat.cast_nonneg n )

/-
A direct version with an already established pointwise `ψ` lower bound.
-/
theorem globalVariancePsi_lower_bound_of_pointwise
    (ratio : Fin N → ℝ) (n : ℕ) {c : ℝ}
    (hpoint : ∀ k, c ≤ gaussianPsi (ratio k)) :
    c * ((N * n : ℕ) : ℝ) ≤ globalVariancePsi ratio n := by
  rw [ globalVariancePsi_eq ];
  simpa [ mul_comm, mul_assoc, mul_left_comm, Finset.mul_sum _ _ _ ] using mul_le_mul_of_nonneg_left ( Finset.sum_le_sum fun i ( hi : i ∈ Finset.univ ) => hpoint i ) ( Nat.cast_nonneg n )

/-
If the innovation-factor ratio is uniformly `η`-close to one, compact
scale separation gives a uniform positive lower bound for every variance
ratio, provided the perturbation is smaller than the scale gap.
-/
theorem global_ou_scale_ratio_separation
    (scaleRatio factorRatio : Fin N → ℝ)
    {delta eta upper eps : ℝ}
    (hscale0 : ∀ k, 0 ≤ scaleRatio k)
    (hscaleUpper : ∀ k, scaleRatio k ≤ upper)
    (hscaleSep : ∀ k, delta ≤ |scaleRatio k - 1|)
    (hfactorClose : ∀ k, |factorRatio k - 1| ≤ eta)
    (heps : eps ≤ delta - upper * eta) :
    ∀ k, eps ≤ |scaleRatio k * factorRatio k - 1| := by
  intros k
  have h_mul_ratio_separated_from_one_k : delta - upper * eta ≤ |scaleRatio k * factorRatio k - 1| := by
    exact mul_ratio_separated_from_one ( hscale0 k ) ( hscaleUpper k ) ( hscaleSep k ) ( hfactorClose k );
  linarith

end

end OperatorInterventions