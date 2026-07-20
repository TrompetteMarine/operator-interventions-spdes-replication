import RequestProject.OUInformation

/-!
# Deterministic argmin consistency and separation

These lemmas isolate the deterministic logic used by Theorem 9.13.  They make
all substantive inputs explicit: a genuine minimizer, deterministic separation,
and uniform approximation.  No desired consistency conclusion is hidden in an
assumption.
-/

namespace OperatorInterventions

/-- Uniform absolute approximation of one criterion by another on a parameter
set. -/
def UniformCriterionError
    {Parameter : Type*} (admissible : Set Parameter)
    (randomCriterion deterministicCriterion : Parameter → ℝ)
    (error : ℝ) : Prop :=
  ∀ theta ∈ admissible,
    |randomCriterion theta - deterministicCriterion theta| ≤ error

/-- Deterministic criterion separation outside a designated good set. -/
def CriterionSeparated
    {Parameter : Type*} (admissible good : Set Parameter)
    (criterion : Parameter → ℝ) (theta0 : Parameter) (gap : ℝ) : Prop :=
  ∀ theta ∈ admissible, theta ∉ good →
    criterion theta0 + gap ≤ criterion theta

/-
A uniform error smaller than half the deterministic separation gap forces
every exact empirical minimizer into the good set.
-/
theorem argmin_mem_of_uniform_error_and_separation
    {Parameter : Type*}
    {admissible good : Set Parameter}
    {randomCriterion deterministicCriterion : Parameter → ℝ}
    {theta0 thetaHat : Parameter} {gap error : ℝ}
    (htheta0 : theta0 ∈ admissible)
    (hthetaHat : thetaHat ∈ admissible)
    (hmin : ∀ theta ∈ admissible,
      randomCriterion thetaHat ≤ randomCriterion theta)
    (hsep : CriterionSeparated admissible good deterministicCriterion theta0 gap)
    (hunif : UniformCriterionError admissible randomCriterion
      deterministicCriterion error)
    (hsmall : 2 * error < gap) :
    thetaHat ∈ good := by
  contrapose! hmin;
  exact ⟨ theta0, htheta0, by linarith [ abs_le.mp ( hunif theta0 htheta0 ), abs_le.mp ( hunif thetaHat hthetaHat ), hsep thetaHat hthetaHat hmin ] ⟩

/-
Metric specialization: deterministic separation outside an `ε`-ball and
uniform criterion control imply the expected finite-stage consistency bound.
-/
theorem argmin_dist_lt_of_uniform_error
    {Parameter : Type*} [PseudoMetricSpace Parameter]
    {admissible : Set Parameter}
    {randomCriterion deterministicCriterion : Parameter → ℝ}
    {theta0 thetaHat : Parameter} {eps gap error : ℝ}
    (htheta0 : theta0 ∈ admissible)
    (hthetaHat : thetaHat ∈ admissible)
    (hmin : ∀ theta ∈ admissible,
      randomCriterion thetaHat ≤ randomCriterion theta)
    (hsep : ∀ theta ∈ admissible, eps ≤ dist theta theta0 →
      deterministicCriterion theta0 + gap ≤ deterministicCriterion theta)
    (hunif : UniformCriterionError admissible randomCriterion
      deterministicCriterion error)
    (hsmall : 2 * error < gap) :
    dist thetaHat theta0 < eps := by
  contrapose! hmin;
  exact ⟨ theta0, htheta0, by linarith [ abs_le.mp ( hunif theta0 htheta0 ), abs_le.mp ( hunif thetaHat hthetaHat ), hsep thetaHat hthetaHat hmin ] ⟩

/-
Product-parameter consistency from separate drift and scale exclusion
bounds.  This is the deterministic assembly needed after the two inequalities
of Lemma 9.7 and stochastic criterion control have been established.
-/
theorem product_argmin_coordinate_bounds
    {randomCriterion deterministicCriterion : (ℝ × ℝ) → ℝ}
    {admissible : Set (ℝ × ℝ)}
    {theta0 sigma0 thetaHat sigmaHat eps gap error : ℝ}
    (htrue : (theta0, sigma0) ∈ admissible)
    (hhat : (thetaHat, sigmaHat) ∈ admissible)
    (hmin : ∀ p ∈ admissible,
      randomCriterion (thetaHat, sigmaHat) ≤ randomCriterion p)
    (hsepTheta : ∀ p ∈ admissible, eps ≤ |p.1 - theta0| →
      deterministicCriterion (theta0, sigma0) + gap ≤
        deterministicCriterion p)
    (hsepSigma : ∀ p ∈ admissible, eps ≤ |p.2 - sigma0| →
      deterministicCriterion (theta0, sigma0) + gap ≤
        deterministicCriterion p)
    (hunif : UniformCriterionError admissible randomCriterion
      deterministicCriterion error)
    (hsmall : 2 * error < gap) :
    |thetaHat - theta0| < eps ∧ |sigmaHat - sigma0| < eps := by
  grind +locals

/-
Coordinatewise bounds imply a Euclidean product-distance bound.
-/
theorem prod_dist_lt_of_coordinate_bounds
    {theta0 sigma0 theta sigma eps : ℝ} (heps : 0 ≤ eps)
    (htheta : |theta - theta0| < eps)
    (hsigma : |sigma - sigma0| < eps) :
    dist (theta, sigma) (theta0, sigma0) < Real.sqrt 2 * eps := by
  convert max_lt _ _ using 1;
  · exact lt_of_lt_of_le htheta ( le_mul_of_one_le_left heps ( Real.le_sqrt_of_sq_le ( by norm_num ) ) );
  · exact lt_of_lt_of_le hsigma ( le_mul_of_one_le_left heps ( Real.le_sqrt_of_sq_le ( by norm_num ) ) )

/-
Sequential consistency theorem: if every fixed-radius deterministic gap
eventually dominates twice the uniform criterion error, exact minimizers
converge to the true parameter.
-/
theorem argmin_tendsto_of_eventual_separation
    {Parameter : Type*} [PseudoMetricSpace Parameter]
    (admissible : Set Parameter)
    (randomCriterion deterministicCriterion : ℕ → Parameter → ℝ)
    (theta0 : Parameter) (thetaHat : ℕ → Parameter)
    (gap error : ℕ → ℝ)
    (htheta0 : theta0 ∈ admissible)
    (hthetaHat : ∀ n, thetaHat n ∈ admissible)
    (hmin : ∀ n theta, theta ∈ admissible →
      randomCriterion n (thetaHat n) ≤ randomCriterion n theta)
    (hunif : ∀ n, UniformCriterionError admissible
      (randomCriterion n) (deterministicCriterion n) (error n))
    (hsep : ∀ eps > 0, ∀ᶠ n in Filter.atTop,
      ∀ theta ∈ admissible, eps ≤ dist theta theta0 →
        deterministicCriterion n theta0 + gap n ≤
          deterministicCriterion n theta)
    (hdom : ∀ᶠ n in Filter.atTop, 2 * error n < gap n) :
    Filter.Tendsto thetaHat Filter.atTop (nhds theta0) := by
  refine' Metric.tendsto_nhds.mpr _;
  intro ε hε;
  filter_upwards [ hsep ε hε, hdom ] with n hn hn' using argmin_dist_lt_of_uniform_error htheta0 ( hthetaHat n ) ( hmin n ) hn ( hunif n ) hn'

end OperatorInterventions