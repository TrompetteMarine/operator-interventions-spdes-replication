import RequestProject.SpectralSummation

/-!
# Modal burn-in and summed second-moment lower bounds

This file formalizes the finite-time lower-bound argument used in the drift
part of Lemma 9.7.  It avoids informal ceiling estimates: a burn-in index is
passed explicitly together with the exact decay inequality it must satisfy.
-/

namespace OperatorInterventions

noncomputable section

/-
Powers of an exact OU transition coefficient decrease with time in the
positive-parameter regime.
-/
theorem ouRho_pow_two_antitone
    {theta lambda delta : ℝ}
    (htheta : 0 < theta) (hlambda : 0 < lambda) (hdelta : 0 ≤ delta) :
    Antitone (fun j : ℕ => (ouRho theta lambda delta) ^ (2 * j)) := by
  exact fun i j hij => pow_le_pow_of_le_one ( by
    exact le_of_lt ( ouRho_pos_le_one htheta hlambda hdelta |>.1 ) ) ( by
    exact ouRho_pos_le_one htheta hlambda hdelta |>.2 ) ( by linarith )

/-
After an explicit burn-in index at which the squared transition power is
at most one half, every later exact modal second moment is at least half the
stationary variance.
-/
theorem half_stationaryVariance_le_ouSecondMoment_of_burnIn
    {theta v q lambda delta u0 : ℝ} {burn j : ℕ}
    (htheta : 0 < theta) (hv : 0 ≤ v) (hlambda : 0 < lambda)
    (hdelta : 0 ≤ delta) (hburn : burn ≤ j)
    (hdecay : (ouRho theta lambda delta) ^ (2 * burn) ≤ 1 / 2) :
    ouStationaryVariance theta v q lambda / 2 ≤
      ouSecondMoment theta v q lambda delta u0 j := by
  unfold ouSecondMoment;
  -- By definition of $ouRho$, we know that $ouRho theta lambda delta ^ (2 * j) \leq ouRho theta lambda delta ^ (2 * burn)$.
  have h_rhost_sq_le : (ouRho theta lambda delta) ^ (2 * j) ≤ (ouRho theta lambda delta) ^ (2 * burn) := by
    exact pow_le_pow_of_le_one ( by exact ( OperatorInterventions.ouRho_pos_le_one htheta hlambda hdelta ) |>.1.le ) ( by exact ( OperatorInterventions.ouRho_pos_le_one htheta hlambda hdelta ) |>.2 ) ( by gcongr );
  nlinarith [ show 0 ≤ ouRho theta lambda delta ^ ( 2 * j ) * u0 ^ 2 by exact mul_nonneg ( pow_mul ( ouRho theta lambda delta ) 2 j ▸ by positivity ) ( sq_nonneg u0 ), show 0 ≤ ouStationaryVariance theta v q lambda by exact div_nonneg ( mul_nonneg hv ( sq_nonneg q ) ) ( mul_nonneg ( mul_nonneg zero_le_two htheta.le ) hlambda.le ) ]

/-
The number of indices in the half-open interval `[burn,n)`.
-/
theorem card_Ico_burnIn (burn n : ℕ) :
    (Finset.Ico burn n).card = n - burn := by
  exact Nat.card_Ico burn n

/-
Summing the post-burn-in observations yields a quantitative modal
second-moment lower bound.
-/
theorem burnIn_sum_ouSecondMoment_lower_bound
    {theta v q lambda delta u0 : ℝ} {burn n : ℕ}
    (htheta : 0 < theta) (hv : 0 ≤ v) (hlambda : 0 < lambda)
    (hdelta : 0 ≤ delta) (hburn : burn ≤ n)
    (hdecay : (ouRho theta lambda delta) ^ (2 * burn) ≤ 1 / 2) :
    ((n - burn : ℕ) : ℝ) *
        (ouStationaryVariance theta v q lambda / 2) ≤
      ∑ j ∈ Finset.Ico burn n,
        ouSecondMoment theta v q lambda delta u0 j := by
  convert Finset.sum_le_sum fun j hj => half_stationaryVariance_le_ouSecondMoment_of_burnIn htheta hv hlambda hdelta ( Finset.mem_Ico.mp hj |>.1 ) hdecay using 1 ; norm_num [ hburn ]

/-
If burn-in consumes at most half the observations, the post-burn-in sum is
at least `n/4` times the stationary variance.
-/
theorem half_sample_sum_ouSecondMoment_lower_bound
    {theta v q lambda delta u0 : ℝ} {burn n : ℕ}
    (htheta : 0 < theta) (hv : 0 ≤ v) (hlambda : 0 < lambda)
    (hdelta : 0 ≤ delta) (hburn : 2 * burn ≤ n)
    (hdecay : (ouRho theta lambda delta) ^ (2 * burn) ≤ 1 / 2) :
    (n : ℝ) * ouStationaryVariance theta v q lambda / 4 ≤
      ∑ j ∈ Finset.Ico burn n,
        ouSecondMoment theta v q lambda delta u0 j := by
  refine le_trans ?_ ( burnIn_sum_ouSecondMoment_lower_bound htheta hv hlambda hdelta ( by linarith ) hdecay );
  rw [ Nat.cast_sub ( by linarith ) ];
  nlinarith [ show ( 0 : ℝ ) ≤ ouStationaryVariance theta v q lambda by exact div_nonneg ( mul_nonneg hv ( sq_nonneg _ ) ) ( mul_nonneg ( mul_nonneg zero_le_two htheta.le ) hlambda.le ), show ( 2 * burn : ℝ ) ≤ n by norm_cast ]

/-
The full observation-time sum dominates its nonnegative post-burn-in
subsum.
-/
theorem full_sum_ge_burnIn_sum
    {theta v q lambda delta u0 : ℝ} {burn n : ℕ}
    (htheta : 0 < theta) (hv : 0 ≤ v) (hlambda : 0 < lambda)
    (hdelta : 0 ≤ delta) :
    (∑ j ∈ Finset.Ico burn n,
      ouSecondMoment theta v q lambda delta u0 j) ≤
    ∑ j ∈ Finset.range n,
      ouSecondMoment theta v q lambda delta u0 j := by
  exact Finset.sum_le_sum_of_subset_of_nonneg ( Finset.subset_iff.mpr fun x hx => Finset.mem_range.mpr ( Finset.mem_Ico.mp hx |>.2 ) ) fun _ _ _ => ouSecondMoment_nonneg htheta hv hlambda hdelta _

/-
Combined full-sample modal lower bound in the form used by the KL drift
separation calculation.
-/
theorem full_sum_ouSecondMoment_lower_bound
    {theta v q lambda delta u0 : ℝ} {burn n : ℕ}
    (htheta : 0 < theta) (hv : 0 ≤ v) (hlambda : 0 < lambda)
    (hdelta : 0 ≤ delta) (hburn : 2 * burn ≤ n)
    (hdecay : (ouRho theta lambda delta) ^ (2 * burn) ≤ 1 / 2) :
    (n : ℝ) * ouStationaryVariance theta v q lambda / 4 ≤
      ∑ j ∈ Finset.range n,
        ouSecondMoment theta v q lambda delta u0 j := by
  refine' le_trans _ ( full_sum_ge_burnIn_sum htheta hv hlambda hdelta );
  convert half_sample_sum_ouSecondMoment_lower_bound htheta hv hlambda hdelta hburn hdecay using 1

end

end OperatorInterventions