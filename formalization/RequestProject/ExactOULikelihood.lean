import RequestProject.ConstrainedMLE

/-!
# Exact finite-dimensional modal OU likelihood

This file formalizes the exact finite-mode conditional experiment from Part S3
of the paper.  The scale parameter here is the variance scale `v = σ²`.  Paths
are indexed by natural times, while both likelihood sums are finite.
-/

namespace OperatorInterventions

noncomputable section

/-- Exact OU transition coefficient `exp (-θ λ Δ)`. -/
def ouRho (theta lambda delta : ℝ) : ℝ :=
  Real.exp (-theta * lambda * delta)

/-- Exact OU innovation time factor `(1-exp(-2θλΔ))/(2θλ)`. -/
def ouInnovationFactor (theta lambda delta : ℝ) : ℝ :=
  (1 - Real.exp (-2 * theta * lambda * delta)) / (2 * theta * lambda)

/-- The exact OU transition coefficient agrees with the foundational spectral definition. -/
theorem ouRho_eq_spectralRho (theta lambda delta : ℝ) :
    ouRho theta lambda delta = spectralRho theta lambda delta := by
  rfl

/-- The exact innovation factor is strictly positive for positive drift,
frequency, and mesh. -/
theorem ouInnovationFactor_pos
    {theta lambda delta : ℝ} (htheta : 0 < theta)
    (hlambda : 0 < lambda) (hdelta : 0 < delta) :
    0 < ouInnovationFactor theta lambda delta := by
  unfold ouInnovationFactor
  exact div_pos
    (by
      have : Real.exp (-2 * theta * lambda * delta) < 1 :=
        Real.exp_lt_one_iff.mpr (by nlinarith [mul_pos htheta hlambda])
      linarith)
    (by nlinarith [mul_pos htheta hlambda])

/-- A positive modal loading gives a positive exact innovation variance factor. -/
theorem ouModalVarianceFactor_pos
    {theta lambda delta q : ℝ} (htheta : 0 < theta)
    (hlambda : 0 < lambda) (hdelta : 0 < delta) (hq : 0 < q) :
    0 < q ^ 2 * ouInnovationFactor theta lambda delta := by
  exact mul_pos (sq_pos_of_pos hq) (ouInnovationFactor_pos htheta hlambda hdelta)

/-- Residual of one exact modal transition. -/
def ouResidual
    (path : Fin N → ℕ → ℝ) (lambda : Fin N → ℝ)
    (theta delta : ℝ) (k : Fin N) (j : ℕ) : ℝ :=
  path k (j + 1) - ouRho theta (lambda k) delta * path k j

/-- Weighted residual sum of squares appearing in the exact profile likelihood. -/
def ouWeightedRSS
    (path : Fin N → ℕ → ℝ) (lambda q : Fin N → ℝ)
    (n : ℕ) (theta delta : ℝ) : ℝ :=
  ∑ k : Fin N, ∑ j ∈ Finset.range n,
    (ouResidual path lambda theta delta k j) ^ 2 /
      ((q k) ^ 2 * ouInnovationFactor theta (lambda k) delta)

/-- Sum of the mode-specific log innovation factors. -/
def ouLogFactorSum
    (lambda q : Fin N → ℝ) (n : ℕ) (theta delta : ℝ) : ℝ :=
  ∑ k : Fin N, (n : ℝ) * Real.log ((q k) ^ 2 * ouInnovationFactor theta (lambda k) delta)

/-- Twice the exact negative conditional log likelihood, up to the universal
Gaussian additive constant, parametrized by variance scale `v = σ²`. -/
def exactOUNegLogLikelihood
    (path : Fin N → ℕ → ℝ) (lambda q : Fin N → ℝ)
    (n : ℕ) (theta v delta : ℝ) : ℝ :=
  ∑ k : Fin N, ∑ j ∈ Finset.range n,
    (Real.log (v * (q k) ^ 2 * ouInnovationFactor theta (lambda k) delta) +
      (ouResidual path lambda theta delta k j) ^ 2 /
        (v * (q k) ^ 2 * ouInnovationFactor theta (lambda k) delta))

/-
Exact algebraic profile decomposition: the scale-dependent part is
`N n log v + RSS(θ)/v`.
-/
theorem exactOUNegLogLikelihood_decomposition
    (path : Fin N → ℕ → ℝ) (lambda q : Fin N → ℝ)
    (n : ℕ) (theta v delta : ℝ)
    (hv : 0 < v)
    (hfactor : ∀ k, 0 < (q k) ^ 2 * ouInnovationFactor theta (lambda k) delta) :
    exactOUNegLogLikelihood path lambda q n theta v delta =
      ((N * n : ℕ) : ℝ) * Real.log v +
        ouWeightedRSS path lambda q n theta delta / v +
        ouLogFactorSum lambda q n theta delta := by
  unfold exactOUNegLogLikelihood ouWeightedRSS ouLogFactorSum;
  simp +decide [ Finset.sum_add_distrib, Finset.mul_sum _ _ _, div_eq_mul_inv, mul_assoc, mul_comm, Real.log_mul, ne_of_gt, * ] ; ring

/-
The weighted RSS is nonnegative when every exact innovation factor and
modal noise coefficient is positive.
-/
theorem ouWeightedRSS_nonneg
    (path : Fin N → ℕ → ℝ) (lambda q : Fin N → ℝ)
    (n : ℕ) (theta delta : ℝ)
    (hfactor : ∀ k, 0 < (q k) ^ 2 * ouInnovationFactor theta (lambda k) delta) :
    0 ≤ ouWeightedRSS path lambda q n theta delta := by
  exact Finset.sum_nonneg fun k _ => Finset.sum_nonneg fun j _ => div_nonneg ( sq_nonneg _ ) ( le_of_lt ( hfactor k ) )

/-
For a positive number of transitions, the pointwise constrained exact scale
minimizer is `RSS/(Nn)` clamped to the admissible compact interval.  This
includes the degenerate zero-residual path.
-/
theorem exactOU_pointwise_constrained_scale
    (path : Fin N → ℕ → ℝ) (lambda q : Fin N → ℝ)
    (n : ℕ) (theta delta lower upper : ℝ)
    (hN : 0 < N) (hn : 0 < n)
    (hlower : 0 < lower) (hlu : lower ≤ upper)
    (hfactor : ∀ k, 0 < (q k) ^ 2 * ouInnovationFactor theta (lambda k) delta) :
    let unconstrained :=
      ouWeightedRSS path lambda q n theta delta / ((N * n : ℕ) : ℝ)
    let constrained := max lower (min upper unconstrained)
    constrained ∈ Set.Icc lower upper ∧
      ∀ v ∈ Set.Icc lower upper,
        exactOUNegLogLikelihood path lambda q n theta constrained delta ≤
          exactOUNegLogLikelihood path lambda q n theta v delta := by
  convert gaussian_profile_pointwise_clamp_nonneg hlower hlu _ _ using 1;
  rotate_left;
  exact 1;
  exact ouWeightedRSS path lambda q n theta delta / ( N * n );
  · norm_num;
  · exact div_nonneg ( ouWeightedRSS_nonneg path lambda q n theta delta hfactor ) ( by positivity );
  · simp +decide [gaussianProfileObjective];
    intro h; refine' forall_congr' fun v => forall_congr' fun hv₁ => forall_congr' fun hv₂ => _; rw [ exactOUNegLogLikelihood_decomposition, exactOUNegLogLikelihood_decomposition ] <;> norm_num [ hlower, hlu, hfactor ] ;
    · field_simp;
    · linarith

/-
The scale constraint is inactive exactly when the unconstrained profile
value belongs to the admissible interval.
-/
theorem exactOU_scale_constraint_inactive_iff
    {rss count lower upper : ℝ} (hlower : lower ≤ upper) :
    max lower (min upper (rss / count)) = rss / count ↔
      rss / count ∈ Set.Icc lower upper := by
  grind


/-- Pointwise constrained scale selector for the exact OU likelihood. -/
def exactOUScaleAt
    (path : Fin N → ℕ → ℝ) (lambda q : Fin N → ℝ) (n : ℕ)
    (delta lower upper theta : ℝ) : ℝ :=
  max lower (min upper
    (ouWeightedRSS path lambda q n theta delta / ((N * n : ℕ) : ℝ)))

/-
Exact specialization of the abstract profiling theorem: minimizing the
pointwise-clamped exact profile produces a joint constrained MLE.
-/
theorem exactOU_corrected_profile_is_joint_min
    (path : Fin N → ℕ → ℝ) (lambda q : Fin N → ℝ)
    (n : ℕ) (delta thetaLower thetaUpper lower upper thetaHat : ℝ)
    (hN : 0 < N) (hn : 0 < n)
    (hlower : 0 < lower) (hlu : lower ≤ upper)
    (hThetaHat : thetaHat ∈ Set.Icc thetaLower thetaUpper)
    (hfactor : ∀ theta ∈ Set.Icc thetaLower thetaUpper, ∀ k,
      0 < (q k) ^ 2 * ouInnovationFactor theta (lambda k) delta)
    (hprofile : ∀ theta ∈ Set.Icc thetaLower thetaUpper,
      exactOUNegLogLikelihood path lambda q n thetaHat
          (exactOUScaleAt path lambda q n delta lower upper thetaHat) delta ≤
        exactOUNegLogLikelihood path lambda q n theta
          (exactOUScaleAt path lambda q n delta lower upper theta) delta) :
    thetaHat ∈ Set.Icc thetaLower thetaUpper ∧
      exactOUScaleAt path lambda q n delta lower upper thetaHat ∈ Set.Icc lower upper ∧
      ∀ theta ∈ Set.Icc thetaLower thetaUpper, ∀ v ∈ Set.Icc lower upper,
        exactOUNegLogLikelihood path lambda q n thetaHat
            (exactOUScaleAt path lambda q n delta lower upper thetaHat) delta ≤
          exactOUNegLogLikelihood path lambda q n theta v delta := by
  refine' ⟨ _, _, fun theta htheta v hv => _ ⟩;
  · exact hThetaHat;
  · exact ⟨ le_max_left _ _, max_le ( by linarith ) ( min_le_left _ _ ) ⟩;
  · refine' le_trans ( hprofile theta htheta ) _;
    convert exactOU_pointwise_constrained_scale path lambda q n theta delta lower upper hN hn hlower hlu ( hfactor theta htheta ) |>.2 v hv using 1

/-
Compactness and continuity give existence of an exact joint constrained
MLE for every finite modal path, provided all innovation variances stay
positive on the parameter rectangle.
-/
theorem exactOU_joint_min_exists
    (path : Fin N → ℕ → ℝ) (lambda q : Fin N → ℝ)
    (n : ℕ) (delta thetaLower thetaUpper lower upper : ℝ)
    (hTheta : thetaLower ≤ thetaUpper) (hlower : 0 < lower)
    (hlu : lower ≤ upper)
    (hfactor : ∀ theta ∈ Set.Icc thetaLower thetaUpper, ∀ k,
      0 < (q k) ^ 2 * ouInnovationFactor theta (lambda k) delta) :
    ∃ thetaHat ∈ Set.Icc thetaLower thetaUpper,
      ∃ vHat ∈ Set.Icc lower upper,
        ∀ theta ∈ Set.Icc thetaLower thetaUpper, ∀ v ∈ Set.Icc lower upper,
          exactOUNegLogLikelihood path lambda q n thetaHat vHat delta ≤
            exactOUNegLogLikelihood path lambda q n theta v delta := by
  have h_continuous : ContinuousOn (fun p : ℝ × ℝ => exactOUNegLogLikelihood path lambda q n p.1 p.2 delta) (Set.Icc thetaLower thetaUpper ×ˢ Set.Icc lower upper) := by
    refine' continuousOn_finset_sum _ fun k _ => continuousOn_finset_sum _ fun j _ => ContinuousOn.add _ _;
    · refine' ContinuousOn.log _ _;
      · refine' ContinuousOn.mul ( ContinuousOn.mul ( continuousOn_snd ) ( continuousOn_const ) ) _;
        refine' ContinuousOn.div _ _ _;
        · fun_prop;
        · exact ContinuousOn.mul ( ContinuousOn.mul continuousOn_const continuousOn_fst ) continuousOn_const;
        · intro x hx; specialize hfactor x.1 hx.1 k; contrapose! hfactor; simp_all +decide [ ouInnovationFactor ] ;
          cases hfactor <;> simp +decide [ * ];
      · exact fun x hx => mul_ne_zero ( mul_ne_zero ( by linarith [ hx.2.1 ] ) ( by specialize hfactor x.1 hx.1 k; aesop ) ) ( by specialize hfactor x.1 hx.1 k; aesop );
    · refine' ContinuousOn.div _ _ _;
      · refine' ContinuousOn.pow _ _;
        refine' ContinuousOn.sub _ _;
        · exact continuousOn_const;
        · exact ContinuousOn.mul ( ContinuousOn.rexp ( ContinuousOn.mul ( continuousOn_fst.neg.mul continuousOn_const ) continuousOn_const ) ) continuousOn_const;
      · refine' ContinuousOn.mul ( ContinuousOn.mul ( continuousOn_snd ) ( continuousOn_const ) ) _;
        refine' ContinuousOn.div _ _ _;
        · fun_prop;
        · fun_prop;
        · intro x hx; specialize hfactor x.1 hx.1 k; unfold ouInnovationFactor at hfactor; aesop;
      · exact fun x hx => mul_ne_zero ( mul_ne_zero ( by linarith [ hx.2.1 ] ) ( by specialize hfactor x.1 hx.1 k; aesop ) ) ( by specialize hfactor x.1 hx.1 k; aesop );
  have := IsCompact.exists_isMinOn ( CompactIccSpace.isCompact_Icc.prod CompactIccSpace.isCompact_Icc ) ⟨ ⟨ thetaLower, lower ⟩, Set.mem_prod.mpr ⟨ Set.left_mem_Icc.mpr hTheta, Set.left_mem_Icc.mpr hlu ⟩ ⟩ h_continuous;
  obtain ⟨ ⟨ x, y ⟩, hx, hy ⟩ := this; exact ⟨ x, hx.1, y, hx.2, fun theta htheta v hv => hy ( Set.mk_mem_prod htheta hv ) ⟩ ;

end

end OperatorInterventions