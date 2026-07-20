import RequestProject.ModalKLSeparation

/-!
# Explicit OU burn-in construction

This file constructs the burn-in index used in the proof of Lemma 9.7 and
verifies its decay and sample-fraction properties with explicit inequalities.
-/

namespace OperatorInterventions

noncomputable section

/-- The first integer observation index at or beyond the half-life of the
squared exact OU transition coefficient. -/
def ouHalfLifeBurnIn (theta lambda delta : ℝ) : ℕ :=
  Nat.ceil (Real.log 2 / (2 * theta * lambda * delta))

/-
The real half-life is below its chosen integer burn-in index.
-/
theorem halfLife_le_burnIn
    (theta lambda delta : ℝ) :
    Real.log 2 / (2 * theta * lambda * delta) ≤
      (ouHalfLifeBurnIn theta lambda delta : ℝ) := by
  exact Nat.le_ceil _

/-
The chosen burn-in makes the squared transition coefficient at most one
half.
-/
theorem ouHalfLifeBurnIn_decay
    {theta lambda delta : ℝ}
    (htheta : 0 < theta) (hlambda : 0 < lambda) (hdelta : 0 < delta) :
    (ouRho theta lambda delta) ^
        (2 * ouHalfLifeBurnIn theta lambda delta) ≤ 1 / 2 := by
  rw [ ← Real.rpow_natCast, Real.rpow_def_of_pos ];
  · rw [ ← Real.log_le_log_iff ( by positivity ) ( by positivity ), Real.log_div ] <;> norm_num;
    unfold ouRho;
    norm_num;
    have := halfLife_le_burnIn theta lambda delta;
    rw [ div_le_iff₀ ] at this <;> first | positivity | linarith;
  · exact Real.exp_pos _

/-
The ceiling construction is at most one observation beyond the real
half-life.
-/
theorem burnIn_lt_halfLife_add_one
    {theta lambda delta : ℝ}
    (htheta : 0 < theta) (hlambda : 0 < lambda) (hdelta : 0 < delta) :
    (ouHalfLifeBurnIn theta lambda delta : ℝ) <
      Real.log 2 / (2 * theta * lambda * delta) + 1 := by
  exact_mod_cast Nat.ceil_lt_add_one ( by positivity )

/-
An explicit real inequality implies that burn-in consumes at most half of
the available integer observations.
-/
theorem two_burnIn_le_of_real_bound
    {theta lambda delta : ℝ} {n : ℕ}
    (htheta : 0 < theta) (hlambda : 0 < lambda) (hdelta : 0 < delta)
    (hsample : Real.log 2 / (theta * lambda * delta) + 2 ≤ (n : ℝ)) :
    2 * ouHalfLifeBurnIn theta lambda delta ≤ n := by
  have := burnIn_lt_halfLife_add_one htheta hlambda hdelta;
  exact Nat.le_of_lt_succ ( by rw [ ← @Nat.cast_lt ℝ ] ; push_cast; ring_nf at *; linarith )

/-
With `n Δ = T`, a simple lower bound on `θ λ T` implies the half-sample
burn-in condition.
-/
theorem two_burnIn_le_of_horizon
    {theta lambda delta T : ℝ} {n : ℕ}
    (htheta : 0 < theta) (hlambda : 0 < lambda) (hdelta : 0 < delta)
    (horizon : (n : ℝ) * delta = T)
    (hn : 2 ≤ n)
    (hgrowth : Real.log 2 * (n : ℝ) ≤ theta * lambda * T) :
    2 * ouHalfLifeBurnIn theta lambda delta ≤ n := by
  apply Nat.le_of_lt_succ;
  rw [ ← @Nat.cast_lt ℝ ] ; norm_num [ ouHalfLifeBurnIn ];
  rw [ ← horizon ] at *;
  rcases n with ( _ | _ | n ) <;> norm_num at *;
  nlinarith [ Nat.ceil_lt_add_one ( show 0 ≤ Real.log 2 / ( 2 * theta * lambda * delta ) by positivity ), show 0 < theta * lambda * delta by positivity, Real.log_pos one_lt_two, mul_div_cancel₀ ( Real.log 2 ) ( show ( 2 * theta * lambda * delta ) ≠ 0 by positivity ) ]

/-
The explicit half-life construction discharges both burn-in premises of
the full modal second-moment lower bound.
-/
theorem full_sum_ouSecondMoment_lower_bound_halfLife
    {theta v q lambda delta u0 : ℝ} {n : ℕ}
    (htheta : 0 < theta) (hv : 0 ≤ v) (hlambda : 0 < lambda)
    (hdelta : 0 < delta)
    (hsample : Real.log 2 / (theta * lambda * delta) + 2 ≤ (n : ℝ)) :
    (n : ℝ) * ouStationaryVariance theta v q lambda / 4 ≤
      ∑ j ∈ Finset.range n,
        ouSecondMoment theta v q lambda delta u0 j := by
  apply full_sum_ouSecondMoment_lower_bound;
  any_goals positivity;
  convert two_burnIn_le_of_real_bound htheta hlambda hdelta hsample;
  exact ouHalfLifeBurnIn_decay htheta hlambda hdelta

/-
The explicit half-life index can be inserted directly into the modewise KL
lower bound; no burn-in assumptions remain in the conclusion.
-/
theorem ouModeMeanKL2_lower_bound_halfLife
    {theta0 v0 theta v vUpper q lambda delta u0 eps thetaUpper T : ℝ}
    {n : ℕ}
    (htheta0 : 0 < theta0) (htheta : 0 < theta)
    (htheta0Upper : theta0 ≤ thetaUpper) (hthetaUpper : theta ≤ thetaUpper)
    (hv0 : 0 < v0) (hv : 0 < v) (hvUpper : v ≤ vUpper)
    (hq : 0 < q) (hlambda : 0 < lambda) (hdelta : 0 < delta)
    (heps : 0 ≤ eps) (hsep : eps ≤ |theta - theta0|)
    (hsample : Real.log 2 / (theta0 * lambda * delta) + 2 ≤ (n : ℝ))
    (horizon : (n : ℝ) * delta = T) :
    Real.exp (-2 * thetaUpper * lambda * delta) *
        v0 * T * eps ^ 2 / (16 * theta0 * vUpper) * lambda ≤
      ouModeMeanKL2 theta0 v0 theta v q lambda delta u0 n := by
  convert ouModeMeanKL2_lower_bound htheta0 htheta htheta0Upper hthetaUpper hv0 hv hvUpper hq hlambda hdelta heps hsep _ _ _ using 1;
  exact ouHalfLifeBurnIn theta0 lambda delta;
  · exact_mod_cast two_burnIn_le_of_real_bound htheta0 hlambda hdelta hsample;
  · convert ouHalfLifeBurnIn_decay htheta0 hlambda hdelta using 1;
  · exact horizon

end

end OperatorInterventions