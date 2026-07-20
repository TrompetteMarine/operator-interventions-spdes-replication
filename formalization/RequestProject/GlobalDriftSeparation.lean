import RequestProject.BurnInConstruction

/-!
# Global finite-modal drift KL separation

This file assembles the modewise half-life estimate with the fixed-spectrum
tail theorem.  It proves an order-`Λ_N` lower bound under explicit uniform mesh
and burn-in conditions, completing the deterministic drift-separation assembly
used in Lemma 9.7.
-/

namespace OperatorInterventions

open Filter

noncomputable section

/-- Sum of the exact transition-mean KL contributions over the first `N`
modes of a fixed spectrum. -/
def globalOUMeanKL2
    (lambda q u0 : ℕ → ℝ) (N n : ℕ)
    (theta0 v0 theta v delta : ℝ) : ℝ :=
  ∑ k ∈ Finset.range N,
    ouModeMeanKL2 theta0 v0 theta v (q k) (lambda k) delta (u0 k) n

/-
Every global mean-KL sum is nonnegative under the positive-parameter
conditions of the exact modal experiment.
-/
theorem globalOUMeanKL2_nonneg
    {lambda q u0 : ℕ → ℝ} {N n : ℕ}
    {theta0 v0 theta v delta : ℝ}
    (htheta0 : 0 < theta0) (hv0 : 0 ≤ v0)
    (htheta : 0 < theta) (hv : 0 < v) (hdelta : 0 < delta)
    (hlambda : ∀ k, 0 < lambda k) :
    0 ≤ globalOUMeanKL2 lambda q u0 N n theta0 v0 theta v delta := by
  exact Finset.sum_nonneg fun k _ => ouModeMeanKL2_nonneg htheta0 hv0 htheta hv ( hlambda k ) hdelta

/-
A uniform upper bound on `λ_k Δ` turns the mode-dependent exponential
factor into a common positive drift-separation constant.
-/
theorem modal_KL_lower_bound_uniform_mesh
    {theta0 v0 theta v vUpper q lambda delta u0 eps thetaUpper T meshBound : ℝ}
    {n : ℕ}
    (htheta0 : 0 < theta0) (htheta : 0 < theta)
    (htheta0Upper : theta0 ≤ thetaUpper) (hthetaUpper : theta ≤ thetaUpper)
    (hv0 : 0 < v0) (hv : 0 < v) (hvUpper : v ≤ vUpper)
    (hq : 0 < q) (hlambda : 0 < lambda) (hdelta : 0 < delta)
    (heps : 0 ≤ eps) (hsep : eps ≤ |theta - theta0|)
    (hmesh : lambda * delta ≤ meshBound)
    (hsample : Real.log 2 / (theta0 * lambda * delta) + 2 ≤ (n : ℝ))
    (horizon : (n : ℝ) * delta = T) :
    Real.exp (-2 * thetaUpper * meshBound) *
        v0 * T * eps ^ 2 / (16 * theta0 * vUpper) * lambda ≤
      ouModeMeanKL2 theta0 v0 theta v q lambda delta u0 n := by
  -- Apply the lower bound theorem for `ouModeMeanKL2` with the given hypotheses.
  have h_lower_bound : Real.exp (-2 * thetaUpper * lambda * delta) * v0 * T * eps ^ 2 / (16 * theta0 * vUpper) * lambda ≤ ouModeMeanKL2 theta0 v0 theta v q lambda delta u0 n := by
    apply_rules [ ouModeMeanKL2_lower_bound_halfLife ];
  refine le_trans ?_ h_lower_bound;
  norm_num [ mul_assoc, mul_comm, mul_left_comm ] at *;
  exact mul_le_mul_of_nonneg_left ( div_le_div_of_nonneg_right ( mul_le_mul_of_nonneg_left ( mul_le_mul_of_nonneg_left ( mul_le_mul_of_nonneg_left ( Real.exp_le_exp.mpr <| by nlinarith [ show 0 ≤ thetaUpper * 2 by linarith ] ) <| by positivity ) <| by nlinarith ) <| by nlinarith ) <| by exact mul_nonneg ( by positivity ) <| by linarith ) <| by positivity;

/-
Finite-stage global drift separation after a fixed low-mode cutoff.
-/
theorem globalOUMeanKL2_tail_lower_bound
    {lambda q u0 : ℕ → ℝ} {N n K : ℕ}
    {theta0 v0 theta v vUpper delta eps thetaUpper T meshBound : ℝ}
    (htheta0 : 0 < theta0) (htheta : 0 < theta)
    (htheta0Upper : theta0 ≤ thetaUpper) (hthetaUpper : theta ≤ thetaUpper)
    (hv0 : 0 < v0) (hv : 0 < v) (hvUpper : v ≤ vUpper)
    (hdelta : 0 < delta) (heps : 0 ≤ eps)
    (hsep : eps ≤ |theta - theta0|)
    (hlambda : ∀ k, 0 < lambda k) (hq : ∀ k, 0 < q k)
    (hmesh : ∀ k, k ∈ Finset.Ico K N → lambda k * delta ≤ meshBound)
    (hsample : ∀ k, k ∈ Finset.Ico K N →
      Real.log 2 / (theta0 * lambda k * delta) + 2 ≤ (n : ℝ))
    (horizon : (n : ℝ) * delta = T) :
    Real.exp (-2 * thetaUpper * meshBound) *
        v0 * T * eps ^ 2 / (16 * theta0 * vUpper) *
          (∑ k ∈ Finset.Ico K N, lambda k) ≤
      globalOUMeanKL2 lambda q u0 N n theta0 v0 theta v delta := by
  rw [ Finset.mul_sum _ _ _ ];
  refine' le_trans ( Finset.sum_le_sum _ ) _;
  use fun k => ouModeMeanKL2 theta0 v0 theta v ( q k ) ( lambda k ) delta ( u0 k ) n;
  · intro k hk; exact modal_KL_lower_bound_uniform_mesh htheta0 htheta htheta0Upper hthetaUpper hv0 hv hvUpper (hq k) (hlambda k) hdelta heps hsep (hmesh k hk) (hsample k hk) horizon;
  · refine' le_trans _ ( Finset.sum_le_sum_of_subset_of_nonneg ( Finset.subset_iff.mpr fun x hx => Finset.mem_range.mpr <| Finset.mem_Ico.mp hx |>.2 ) fun _ _ _ => _ );
    congr! 1;
    apply_rules [ OperatorInterventions.ouModeMeanKL2_nonneg ];
    grind

/-
Eventual order-`Λ_N` global drift separation for a fixed spectrum.  The
uniform mesh and burn-in premises are stated exactly on the high-mode tail
where they are used.
-/
theorem globalOUMeanKL2_eventual_separation
    {lambda q u0 : ℕ → ℝ} {n K : ℕ}
    {theta0 v0 theta v vUpper delta eps thetaUpper T meshBound : ℝ}
    (htheta0 : 0 < theta0) (htheta : 0 < theta)
    (htheta0Upper : theta0 ≤ thetaUpper) (hthetaUpper : theta ≤ thetaUpper)
    (hv0 : 0 < v0) (hv : 0 < v) (hvUpper : v ≤ vUpper)
    (hdelta : 0 < delta) (heps : 0 ≤ eps)
    (hsep : eps ≤ |theta - theta0|)
    (hlambda : ∀ k, 0 < lambda k) (hq : ∀ k, 0 < q k)
    (hdiv : Tendsto (spectralPartialSum lambda) atTop atTop)
    (hmesh : ∀ k, K ≤ k → lambda k * delta ≤ meshBound)
    (hsample : ∀ k, K ≤ k →
      Real.log 2 / (theta0 * lambda k * delta) + 2 ≤ (n : ℝ))
    (horizon : (n : ℝ) * delta = T) :
    ∀ᶠ N in atTop,
      Real.exp (-2 * thetaUpper * meshBound) *
          v0 * T * eps ^ 2 / (32 * theta0 * vUpper) *
            spectralPartialSum lambda N ≤
        globalOUMeanKL2 lambda q u0 N n theta0 v0 theta v delta := by
  obtain ⟨N₁, hN₁⟩ : ∃ N₁, ∀ N ≥ N₁, (1 / 2 : ℝ) * (∑ k ∈ Finset.range N, lambda k) ≤ (∑ k ∈ Finset.Ico K N, lambda k) := by
    convert spectral_tail_ge_half_eventually hdiv K using 1;
    norm_num [ div_eq_inv_mul, spectralPartialSum ];
  obtain ⟨N₂, hN₂⟩ : ∃ N₂, ∀ N ≥ N₂, (∑ k ∈ Finset.Ico K N, lambda k) * (Real.exp (-2 * thetaUpper * meshBound) * v0 * T * eps ^ 2 / (16 * theta0 * vUpper)) ≤ globalOUMeanKL2 lambda q u0 N n theta0 v0 theta v delta := by
    exact ⟨ K, fun N hN => by simpa only [ mul_comm ] using globalOUMeanKL2_tail_lower_bound htheta0 htheta htheta0Upper hthetaUpper hv0 hv hvUpper hdelta heps hsep hlambda hq ( fun k hk => hmesh k ( Finset.mem_Ico.mp hk |>.1 ) ) ( fun k hk => hsample k ( Finset.mem_Ico.mp hk |>.1 ) ) horizon ⟩;
  filter_upwards [ Filter.eventually_ge_atTop N₁, Filter.eventually_ge_atTop N₂ ] with N hN₁' hN₂' ; specialize hN₁ N hN₁' ; specialize hN₂ N hN₂' ; norm_num [ spectralPartialSum ] at *;
  convert hN₂.trans' ( mul_le_mul_of_nonneg_right hN₁ <| show 0 ≤ Real.exp ( - ( 2 * thetaUpper * meshBound ) ) * v0 * T * eps ^ 2 / ( 16 * theta0 * vUpper ) by exact div_nonneg ( mul_nonneg ( mul_nonneg ( mul_nonneg ( Real.exp_nonneg _ ) ( by positivity ) ) ( by nlinarith ) ) ( sq_nonneg _ ) ) ( by exact mul_nonneg ( by positivity ) ( by linarith ) ) ) using 1 ; ring

end

end OperatorInterventions