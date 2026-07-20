import RequestProject.ExactOULikelihood

/-!
# Gaussian Kullback--Leibler separation core

This file develops the elementary analytic layer needed by Lemma 9.7.  It does
not assume the desired separation conclusion: positivity and compact-uniform
separation are derived from the logarithm inequality.
-/

namespace OperatorInterventions

noncomputable section

/-- The scalar variance-ratio contribution to twice the Gaussian KL divergence. -/
def gaussianPsi (x : ℝ) : ℝ := x - 1 - Real.log x

/-
`ψ(x) = x - 1 - log x` is nonnegative on the positive half-line.
-/
theorem gaussianPsi_nonneg {x : ℝ} (hx : 0 < x) : 0 ≤ gaussianPsi x := by
  exact sub_nonneg_of_le ( by linarith [ Real.log_le_sub_one_of_pos hx ] )

/-
The only positive zero of the Gaussian variance contrast is one.
-/
theorem gaussianPsi_eq_zero_iff {x : ℝ} (hx : 0 < x) :
    gaussianPsi x = 0 ↔ x = 1 := by
  by_cases h : x = 1 <;> simp_all +decide [ gaussianPsi ];
  linarith [ Real.log_lt_sub_one_of_pos hx h ]

/-
Away from one, `ψ` has a strictly positive lower bound on every positive
compact interval.  The explicit nonemptiness hypothesis avoids a vacuous
choice of a minimum when the separated subset is empty.
-/
theorem gaussianPsi_uniform_separation
    {a b eps : ℝ} (ha : 0 < a) (heps : 0 < eps)
    (hne : Set.Nonempty {x | x ∈ Set.Icc a b ∧ eps ≤ |x - 1|}) :
    ∃ c > 0, ∀ x ∈ Set.Icc a b, eps ≤ |x - 1| → c ≤ gaussianPsi x := by
  -- Since $K$ is compact and $gaussianPsi$ is continuous on $K$, we can apply the extreme value theorem to obtain a minimum value $c$.
  obtain ⟨c, hc⟩ : ∃ c ∈ (Set.image gaussianPsi {x ∈ Set.Icc a b | eps ≤ |x - 1|}), ∀ y ∈ (Set.image gaussianPsi {x ∈ Set.Icc a b | eps ≤ |x - 1|}), c ≤ y := by
    apply_rules [ IsCompact.exists_isLeast, CompactIccSpace.isCompact_Icc ];
    · refine' IsCompact.image_of_continuousOn _ _;
      · exact CompactIccSpace.isCompact_Icc.inter_right ( isClosed_le continuous_const <| continuous_abs.comp <| continuous_sub_right _ );
      · exact ContinuousOn.sub ( continuousOn_id.sub continuousOn_const ) ( ContinuousOn.log continuousOn_id fun x hx => ne_of_gt <| lt_of_lt_of_le ha hx.1.1 );
    · exact hne.image _;
  -- Since $c$ is in the image of $gaussianPsi$ over $K$, there exists some $x₀ \in K$ such that $gaussianPsi x₀ = c$.
  obtain ⟨x₀, hx₀K, hx₀c⟩ : ∃ x₀ ∈ {x ∈ Set.Icc a b | eps ≤ |x - 1|}, gaussianPsi x₀ = c := by
    exact hc.1;
  refine' ⟨ c, _, _ ⟩;
  · exact hx₀c ▸ lt_of_le_of_ne ( gaussianPsi_nonneg ( by linarith [ hx₀K.1.1 ] ) ) ( Ne.symm <| by intro H; exact absurd ( gaussianPsi_eq_zero_iff ( by linarith [ hx₀K.1.1 ] ) |>.1 H ) ( by cases abs_cases ( x₀ - 1 ) <;> linarith [ hx₀K.2 ] ) );
  · exact fun x hx₁ hx₂ => hc.2 _ ⟨ x, ⟨ hx₁, hx₂ ⟩, rfl ⟩

/-- Twice the KL divergence from `N(mu0,v0)` to `N(mu,v)`, written without
probability-space infrastructure. -/
def gaussianKL2 (mu0 v0 mu v : ℝ) : ℝ :=
  Real.log (v / v0) + v0 / v - 1 + (mu - mu0) ^ 2 / v

/-
Exact Gaussian KL decomposition into variance and mean separation.
-/
theorem gaussianKL2_decomposition
    {mu0 v0 mu v : ℝ} (hv0 : 0 < v0) (hv : 0 < v) :
    gaussianKL2 mu0 v0 mu v =
      gaussianPsi (v0 / v) + (mu - mu0) ^ 2 / v := by
  unfold gaussianKL2 gaussianPsi
  rw [Real.log_div (ne_of_gt hv) (ne_of_gt hv0),
    Real.log_div (ne_of_gt hv0) (ne_of_gt hv)]
  ring

/-
Gaussian KL is nonnegative for positive variances.
-/
theorem gaussianKL2_nonneg
    {mu0 v0 mu v : ℝ} (hv0 : 0 < v0) (hv : 0 < v) :
    0 ≤ gaussianKL2 mu0 v0 mu v := by
  rw [ gaussianKL2_decomposition hv0 hv ];
  exact add_nonneg ( gaussianPsi_nonneg ( div_pos hv0 hv ) ) ( div_nonneg ( sq_nonneg _ ) hv.le )

/-
Equality in the Gaussian KL contrast identifies both the mean and the
variance.
-/
theorem gaussianKL2_eq_zero_iff
    {mu0 v0 mu v : ℝ} (hv0 : 0 < v0) (hv : 0 < v) :
    gaussianKL2 mu0 v0 mu v = 0 ↔ mu = mu0 ∧ v = v0 := by
  -- By Gaussian KL decomposition, equality forces both summands to be zero.
  apply Iff.intro
  intro h_eq_zero
  have h_var : gaussianPsi (v0 / v) = 0 := by
    rw [ gaussianKL2_decomposition hv0 hv ] at h_eq_zero;
    exact le_antisymm ( le_trans ( le_add_of_nonneg_right <| by positivity ) h_eq_zero.le ) ( gaussianPsi_nonneg <| by positivity )
  have h_mean : (mu - mu0)^2 / v = 0 := by
    grind +suggestions
  have h_v : v0 / v = 1 := by
    exact gaussianPsi_eq_zero_iff ( div_pos hv0 hv ) |>.1 h_var
  have h_mu : mu = mu0 := by
    simpa [ sub_eq_iff_eq_add, hv.ne' ] using h_mean
  exact ⟨h_mu, by
    grind⟩
  intro h
  simp [gaussianKL2] at *;
  simp_all +decide [ ne_of_gt ]

/-
A finite sum of exact Gaussian KL contributions is nonnegative.
-/
theorem finite_gaussianKL2_sum_nonneg
    {ι : Type*} [Fintype ι]
    (mu0 v0 mu v : ι → ℝ)
    (hv0 : ∀ i, 0 < v0 i) (hv : ∀ i, 0 < v i) :
    0 ≤ ∑ i, gaussianKL2 (mu0 i) (v0 i) (mu i) (v i) := by
  exact Finset.sum_nonneg fun i _ => gaussianKL2_nonneg ( hv0 i ) ( hv i )

/-
If a finite Gaussian KL sum vanishes, every modal mean and variance agrees.
This is the exact finite-dimensional identification step behind global KL
separation.
-/
theorem finite_gaussianKL2_sum_eq_zero_iff
    {ι : Type*} [Fintype ι]
    (mu0 v0 mu v : ι → ℝ)
    (hv0 : ∀ i, 0 < v0 i) (hv : ∀ i, 0 < v i) :
    (∑ i, gaussianKL2 (mu0 i) (v0 i) (mu i) (v i) = 0) ↔
      ∀ i, mu i = mu0 i ∧ v i = v0 i := by
  rw [ Finset.sum_eq_zero_iff_of_nonneg ];
  · simp +decide [ gaussianKL2_eq_zero_iff ( hv0 _ ) ( hv _ ) ];
  · exact fun i _ => gaussianKL2_nonneg ( hv0 i ) ( hv i )

end

end OperatorInterventions