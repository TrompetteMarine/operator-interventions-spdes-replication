import RequestProject.GaussianKL

/-!
# Exact finite-modal OU Kullback--Leibler contrast

This file instantiates the Gaussian KL core with the exact OU transition means
and variances.  It supplies the exact finite-sample decomposition used before
any asymptotic lower bound in Lemma 9.7.
-/

namespace OperatorInterventions

noncomputable section

/-- Exact modal transition variance under variance scale `v = σ²`. -/
def ouTransitionVariance
    (lambda q : Fin N → ℝ) (theta v delta : ℝ) (k : Fin N) : ℝ :=
  v * (q k) ^ 2 * ouInnovationFactor theta (lambda k) delta

/-- Twice the conditional Gaussian KL contrast for all observed transitions,
conditional on the displayed lagged modal values. -/
def exactOUConditionalKL2
    (lagged : Fin N → ℕ → ℝ) (lambda q : Fin N → ℝ) (n : ℕ)
    (theta0 v0 theta v delta : ℝ) : ℝ :=
  ∑ k : Fin N, ∑ j ∈ Finset.range n,
    gaussianKL2
      (ouRho theta0 (lambda k) delta * lagged k j)
      (ouTransitionVariance lambda q theta0 v0 delta k)
      (ouRho theta (lambda k) delta * lagged k j)
      (ouTransitionVariance lambda q theta v delta k)

/-
The exact OU conditional KL is the sum of a variance-ratio contrast and a
nonnegative squared transition-mean contrast.
-/
theorem exactOUConditionalKL2_decomposition
    (lagged : Fin N → ℕ → ℝ) (lambda q : Fin N → ℝ) (n : ℕ)
    (theta0 v0 theta v delta : ℝ)
    (hvar0 : ∀ k, 0 < ouTransitionVariance lambda q theta0 v0 delta k)
    (hvar : ∀ k, 0 < ouTransitionVariance lambda q theta v delta k) :
    exactOUConditionalKL2 lagged lambda q n theta0 v0 theta v delta =
      ∑ k : Fin N, ∑ j ∈ Finset.range n,
        (gaussianPsi
            (ouTransitionVariance lambda q theta0 v0 delta k /
              ouTransitionVariance lambda q theta v delta k) +
          ((ouRho theta (lambda k) delta - ouRho theta0 (lambda k) delta) *
            lagged k j) ^ 2 /
              ouTransitionVariance lambda q theta v delta k) := by
  refine' Finset.sum_congr rfl fun k hk => Finset.sum_congr rfl fun j hj => _;
  convert gaussianKL2_decomposition ( hvar0 k ) ( hvar k ) using 1 ; ring

/-
Every exact finite-modal conditional KL contrast is nonnegative.
-/
theorem exactOUConditionalKL2_nonneg
    (lagged : Fin N → ℕ → ℝ) (lambda q : Fin N → ℝ) (n : ℕ)
    (theta0 v0 theta v delta : ℝ)
    (hvar0 : ∀ k, 0 < ouTransitionVariance lambda q theta0 v0 delta k)
    (hvar : ∀ k, 0 < ouTransitionVariance lambda q theta v delta k) :
    0 ≤ exactOUConditionalKL2 lagged lambda q n theta0 v0 theta v delta := by
  exact Finset.sum_nonneg fun i hi => Finset.sum_nonneg fun j hj => gaussianKL2_nonneg ( hvar0 i ) ( hvar i )

/-
Vanishing finite OU conditional KL is equivalent to equality of every
conditional transition mean and variance represented in the finite sample.
-/
theorem exactOUConditionalKL2_eq_zero_iff
    (lagged : Fin N → ℕ → ℝ) (lambda q : Fin N → ℝ) (n : ℕ)
    (theta0 v0 theta v delta : ℝ)
    (hvar0 : ∀ k, 0 < ouTransitionVariance lambda q theta0 v0 delta k)
    (hvar : ∀ k, 0 < ouTransitionVariance lambda q theta v delta k) :
    exactOUConditionalKL2 lagged lambda q n theta0 v0 theta v delta = 0 ↔
      ∀ k : Fin N, ∀ j ∈ Finset.range n,
        ouRho theta (lambda k) delta * lagged k j =
            ouRho theta0 (lambda k) delta * lagged k j ∧
          ouTransitionVariance lambda q theta v delta k =
            ouTransitionVariance lambda q theta0 v0 delta k := by
  constructor <;> intro h;
  · intro k j hj;
    apply (gaussianKL2_eq_zero_iff (hvar0 k) (hvar k)).mp;
    unfold exactOUConditionalKL2 at h;
    rw [ Finset.sum_eq_zero_iff_of_nonneg fun i _ => Finset.sum_nonneg fun j _ => gaussianKL2_nonneg ( hvar0 i ) ( hvar i ) ] at h;
    exact Finset.sum_eq_zero_iff_of_nonneg ( fun _ _ => gaussianKL2_nonneg ( hvar0 k ) ( hvar k ) ) |>.1 ( h k ( Finset.mem_univ k ) ) j hj;
  · exact Finset.sum_eq_zero fun i hi => Finset.sum_eq_zero fun j hj => by have := h i j hj; rw [ gaussianKL2_eq_zero_iff ( hvar0 i ) ( hvar i ) ] ; aesop;

/-
One nonzero lagged observation in a positive-frequency mode identifies the
drift from equality of exact transition means.
-/
theorem ou_drift_eq_of_transition_mean_eq
    {theta0 theta lambda delta y : ℝ}
    (hlambda : 0 < lambda) (hdelta : 0 < delta) (hy : y ≠ 0)
    (hmean : ouRho theta lambda delta * y = ouRho theta0 lambda delta * y) :
    theta = theta0 := by
  simp_all +decide [ouRho];
  aesop

/-
Once drift is identified, equality of a positive modal transition variance
identifies the variance scale.
-/
theorem ou_scale_eq_of_transition_variance_eq
    {theta v0 v lambda q delta : ℝ}
    (htheta : 0 < theta) (hlambda : 0 < lambda) (hq : 0 < q)
    (hdelta : 0 < delta)
    (hvar : v * q ^ 2 * ouInnovationFactor theta lambda delta =
      v0 * q ^ 2 * ouInnovationFactor theta lambda delta) :
    v = v0 := by
  exact mul_left_cancel₀ ( show q ^ 2 * ouInnovationFactor theta lambda delta ≠ 0 from mul_ne_zero ( pow_ne_zero 2 hq.ne' ) ( ne_of_gt ( ouInnovationFactor_pos htheta hlambda hdelta ) ) ) ( by linarith )

/-
A zero exact conditional KL contrast identifies drift and variance scale as
soon as the finite path contains one nonzero lagged observation in a positive
frequency mode.
-/
theorem exactOUConditionalKL2_identifies_parameters
    (lagged : Fin N → ℕ → ℝ) (lambda q : Fin N → ℝ) (n : ℕ)
    (theta0 v0 theta v delta : ℝ)
    (htheta0 : 0 < theta0) (htheta : 0 < theta)
    (hdelta : 0 < delta)
    (hlambda : ∀ k, 0 < lambda k) (hq : ∀ k, 0 < q k)
    (hv0 : 0 < v0) (hv : 0 < v)
    (k : Fin N) (j : ℕ) (hj : j ∈ Finset.range n)
    (hy : lagged k j ≠ 0)
    (hzero : exactOUConditionalKL2 lagged lambda q n
      theta0 v0 theta v delta = 0) :
    theta = theta0 ∧ v = v0 := by
  obtain ⟨hmean, hvar⟩ : ouRho theta (lambda k) delta * lagged k j = ouRho theta0 (lambda k) delta * lagged k j ∧ ouTransitionVariance lambda q theta v delta k = ouTransitionVariance lambda q theta0 v0 delta k := by
    apply (exactOUConditionalKL2_eq_zero_iff lagged lambda q n theta0 v0 theta v delta (by
    exact fun k => mul_pos ( mul_pos hv0 ( sq_pos_of_pos ( hq k ) ) ) ( ouInnovationFactor_pos htheta0 ( hlambda k ) hdelta )) (by
    exact fun k => mul_pos ( mul_pos hv ( sq_pos_of_pos ( hq k ) ) ) ( ouInnovationFactor_pos htheta ( hlambda k ) hdelta ))).mp hzero k j hj;
  have htheta_eq : theta = theta0 := by
    apply ou_drift_eq_of_transition_mean_eq (hlambda k) hdelta hy hmean;
  unfold ouTransitionVariance at hvar; simp_all +decide [ne_of_gt, mul_assoc, mul_comm];
  exact hvar.resolve_right ( ne_of_gt ( ouInnovationFactor_pos htheta0 ( hlambda k ) hdelta ) )

end

end OperatorInterventions