import RequestProject.ConstrainedMLE

/-!
# Audited deterministic cores of pending proofs

The paper's pending stochastic theorems depend on substantial probability and
SPDE infrastructure.  This file formalizes deterministic implications used in
three of those proofs without replacing the missing weak-convergence,
martingale-moment, or analytic approximation premises by hidden axioms.

* `strict_null_positive_part_vanishes` is the decisive deterministic step in
  Theorem 9.22(i).
* `max_fourth_power_le_sum` and `max_norm_le_fourth_sum` are the no-dominance
  implication used in Lemma 9.11.
* `three_stage_approximation` and `three_stage_derivative_approximation` are
  the triangle-inequality assembly in Theorem 9.43.
-/

namespace OperatorInterventions

section ContactSet

/-
Under a uniformly strict null, a uniformly bounded perturbation cannot make
any scaled effect positive.  In the stochastic theorem the bound on `z` is the
high-probability event supplied by tightness of the normalized error process.
-/
theorem strict_null_positive_part_vanishes
    {Index : Type*} {effect error : Index → ℝ} {scale gap : ℝ}
    (hscale : 0 ≤ scale)
    (hnull : ∀ i, effect i ≤ -gap)
    (herror : ∀ i, error i < scale * gap) :
    ∀ i, max (scale * effect i + error i) 0 = 0 := by
  exact fun i => max_eq_right ( by nlinarith [ hnull i, herror i ] )

/-
On the contact set, where the null effect is exactly zero, the positive
part of the scaled estimator is exactly the positive part of its normalized
error.  This is the lower-bound identity in Theorem 9.22(ii).
-/
theorem contact_set_positive_part
    {Index : Type*} {effect error : Index → ℝ} {scale : ℝ}
    {contact : Set Index}
    (hcontact : ∀ i ∈ contact, effect i = 0) :
    ∀ i ∈ contact,
      max (scale * effect i + error i) 0 = max (error i) 0 := by
  grind +qlia

/-
The positive-part map is one-Lipschitz; this is the elementary continuity
input for the supremum functional in the contact-set argument.
-/
theorem positive_part_lipschitz (x y : ℝ) :
    |max x 0 - max y 0| ≤ |x - y| := by
  grind

end ContactSet

section ModeBlockNoDominance

variable {E : Type*} [SeminormedAddCommGroup E]

/-
The largest fourth power in a finite family is bounded by their sum.
-/
theorem max_fourth_power_le_sum
    {Index : Type*} (s : Finset Index) (x : Index → E) (i : Index)
    (hi : i ∈ s) :
    ‖x i‖ ^ 4 ≤ ∑ k ∈ s, ‖x k‖ ^ 4 := by
  exact Finset.single_le_sum ( fun k _ => pow_nonneg ( norm_nonneg ( x k ) ) 4 ) hi

/-
Quantitative no-dominance consequence of a summed fourth-moment bound.
This is the deterministic inequality underneath Markov's inequality in the
passage from (158) to (159).
-/
theorem max_norm_le_fourth_sum
    {Index : Type*} (s : Finset Index) (x : Index → E) (bound : ℝ)
    (hbound : ∑ k ∈ s, ‖x k‖ ^ 4 ≤ bound) (i : Index) (hi : i ∈ s) :
    ‖x i‖ ≤ Real.sqrt (Real.sqrt (max bound 0)) := by
  refine' Real.le_sqrt_of_sq_le ( Real.le_sqrt_of_sq_le _ );
  exact le_trans ( by rw [ ← pow_mul ] ) ( le_trans ( Finset.single_le_sum ( fun a _ => by positivity ) hi ) ( le_max_of_le_left hbound ) )

end ModeBlockNoDominance

section ApproximationAssembly

variable {E : Type*} [SeminormedAddCommGroup E]

/-
Triangle-inequality assembly for the three approximation stages in
Theorem 9.43: intervention discretization, temporal approximation, and spatial
truncation.
-/
theorem three_stage_approximation
    (exact spatial temporal implemented : E)
    {spatialError temporalError interventionError : ℝ}
    (hspatial : ‖spatial - exact‖ ≤ spatialError)
    (htemporal : ‖temporal - spatial‖ ≤ temporalError)
    (hintervention : ‖implemented - temporal‖ ≤ interventionError) :
    ‖implemented - exact‖ ≤
      spatialError + temporalError + interventionError := by
  have h_triangle : ‖implemented - exact‖ ≤ ‖implemented - temporal‖ + ‖temporal - spatial‖ + ‖spatial - exact‖ := by
    simpa only [ ← dist_eq_norm, dist_triangle ] using dist_triangle4 _ _ _ _;
  linarith

/-
The same assembly applies to Fréchet derivatives once each primitive
approximation has been proved in the derivative norm.
-/
theorem three_stage_derivative_approximation
    (exactD spatialD temporalD implementedD : E)
    {spatialError temporalError interventionError : ℝ}
    (hspatial : ‖spatialD - exactD‖ ≤ spatialError)
    (htemporal : ‖temporalD - spatialD‖ ≤ temporalError)
    (hintervention : ‖implementedD - temporalD‖ ≤ interventionError) :
    ‖implementedD - exactD‖ ≤
      spatialError + temporalError + interventionError := by
  exact three_stage_approximation exactD spatialD temporalD implementedD
    hspatial htemporal hintervention

end ApproximationAssembly

end OperatorInterventions