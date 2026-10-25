import RequestProject.OUSmallMesh

/-!
# Spectral tail summation

This file formalizes the deterministic high-mode summation step used in the
proof of global drift separation.  A fixed finite collection of low modes is
shown to be negligible relative to a divergent positive spectral partial sum.
-/

namespace OperatorInterventions

open Filter

/-- Partial sum of a fixed spectrum over the first `N` modes. -/
def spectralPartialSum (lambda : ℕ → ℝ) (N : ℕ) : ℝ :=
  ∑ k ∈ Finset.range N, lambda k

/-
Exact decomposition into a fixed prefix and the remaining modes.
-/
theorem spectralPartialSum_prefix_tail
    (lambda : ℕ → ℝ) {K N : ℕ} (hKN : K ≤ N) :
    spectralPartialSum lambda N =
      spectralPartialSum lambda K +
        ∑ k ∈ Finset.Ico K N, lambda k := by
  unfold spectralPartialSum; rw [ Finset.range_eq_Ico, Finset.sum_Ico_consecutive ] <;> linarith;

/-
A nonnegative spectrum has monotone partial sums.
-/
theorem spectralPartialSum_mono
    {lambda : ℕ → ℝ} (hlambda : ∀ k, 0 ≤ lambda k) :
    Monotone (spectralPartialSum lambda) := by
  exact fun m n mn => Finset.sum_le_sum_of_subset_of_nonneg ( Finset.range_mono mn ) fun _ _ _ => hlambda _

/-
Every fixed finite prefix is eventually at most half of a divergent
spectral partial sum.
-/
theorem spectral_prefix_le_half_eventually
    {lambda : ℕ → ℝ}
    (hdiv : Tendsto (spectralPartialSum lambda) atTop atTop)
    (K : ℕ) :
    ∀ᶠ N in atTop,
      2 * spectralPartialSum lambda K ≤ spectralPartialSum lambda N := by
  exact hdiv.eventually_ge_atTop _

/-
Consequently, at least half of a divergent nonnegative spectral mass is
carried by modes above any fixed cutoff.
-/
theorem spectral_tail_ge_half_eventually
    {lambda : ℕ → ℝ}
    (hdiv : Tendsto (spectralPartialSum lambda) atTop atTop)
    (K : ℕ) :
    ∀ᶠ N in atTop,
      spectralPartialSum lambda N / 2 ≤
        ∑ k ∈ Finset.Ico K N, lambda k := by
  have hprefix_le_half := spectral_prefix_le_half_eventually hdiv K;
  filter_upwards [ hprefix_le_half, Filter.eventually_ge_atTop K ] with N hN₁ hN₂;
  linarith [ spectralPartialSum_prefix_tail lambda hN₂ ]

/-
Pointwise lower bounds proportional to modal frequency sum to an
order-`Λ_N` lower bound when all contributions are nonnegative.  The
nonnegativity assumption is necessary to pass from the high-mode tail to the
full modal sum.
-/
theorem sum_ge_half_spectralPartialSum_eventually
    {lambda contribution : ℕ → ℝ}
    (hdiv : Tendsto (spectralPartialSum lambda) atTop atTop)
    {c : ℝ} (hc : 0 ≤ c) (K : ℕ)
    (hnonneg : ∀ k, 0 ≤ contribution k)
    (hcontribution : ∀ k, K ≤ k → c * lambda k ≤ contribution k) :
    ∀ᶠ N in atTop,
      c * spectralPartialSum lambda N / 2 ≤
        ∑ k ∈ Finset.range N, contribution k := by
  -- Use `spectral_tail_ge_half_eventually` to get that for sufficiently large N, the sum of lambda k from K to N-1 is at least half of the total sum.
  have h_tail : ∀ᶠ N in Filter.atTop, ∑ k ∈ Finset.Ico K N, lambda k ≥ spectralPartialSum lambda N / 2 := by
    convert spectral_tail_ge_half_eventually hdiv K using 1;
  filter_upwards [ h_tail, Filter.eventually_ge_atTop K ] with N hN hN';
  refine' le_trans _ ( Finset.sum_le_sum_of_subset_of_nonneg ( show Finset.Ico K N ⊆ Finset.range N from fun x hx => Finset.mem_range.mpr <| Finset.mem_Ico.mp hx |>.2 ) fun _ _ _ => hnonneg _ );
  exact le_trans ( by rw [ ← Finset.mul_sum _ _ _ ] ; nlinarith ) ( Finset.sum_le_sum fun i hi => hcontribution i <| Finset.mem_Ico.mp hi |>.1 )

/-- A low-mode negative contribution used to demonstrate that `hnonneg` in
`sum_ge_half_spectralPartialSum_eventually` cannot simply be omitted. -/
def lowModeNegativeContribution (k : ℕ) : ℝ :=
  if k = 0 then -1 else 0

/-
Verified counterexample to the version of the preceding theorem without
nonnegativity: the tail condition holds with `c = 0` and cutoff one, but the
full sums remain negative.
-/
theorem low_mode_nonnegativity_is_necessary :
    (∀ k, 1 ≤ k → (0 : ℝ) * 1 ≤ lowModeNegativeContribution k) ∧
    ∀ N, 1 ≤ N →
      ¬((0 : ℝ) * spectralPartialSum (fun _ => 1) N / 2 ≤
        ∑ k ∈ Finset.range N, lowModeNegativeContribution k) := by
  unfold lowModeNegativeContribution; norm_num;
  grind

/-
A version where the lower bound is only needed on the explicit tail
finset, convenient for modal likelihood sums.
-/
theorem tail_sum_ge_half_spectralPartialSum_eventually
    {lambda contribution : ℕ → ℝ}
    (hdiv : Tendsto (spectralPartialSum lambda) atTop atTop)
    {c : ℝ} (hc : 0 ≤ c) (K : ℕ)
    (hcontribution : ∀ k, K ≤ k → c * lambda k ≤ contribution k) :
    ∀ᶠ N in atTop,
      c * spectralPartialSum lambda N / 2 ≤
        ∑ k ∈ Finset.Ico K N, contribution k := by
  have h_tail_bound : ∀ᶠ N in atTop, c * (∑ k ∈ Finset.Ico K N, lambda k) ≥ c * (spectralPartialSum lambda N) / 2 := by
    filter_upwards [ spectral_tail_ge_half_eventually hdiv K ] with N hN using by nlinarith;
  filter_upwards [ h_tail_bound ] with N hN using le_trans hN ( by simpa only [ Finset.mul_sum _ _ _ ] using Finset.sum_le_sum fun k hk => hcontribution k <| Finset.mem_Ico.mp hk |>.1 )

end OperatorInterventions