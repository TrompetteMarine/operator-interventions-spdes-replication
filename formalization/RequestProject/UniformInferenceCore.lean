import RequestProject.PendingProofCores

/-!
# Deterministic core for derivative-zero robust inference

These lemmas formalize the normalization argument used in Theorem 9.26.  They
do not assert the missing stochastic expansion or bootstrap convergence.
-/

namespace OperatorInterventions

/-
Cauchy--Schwarz remains informative at derivative zeros: if the loading
norm is bounded by a positive floor weight, its studentized linear functional
is globally bounded by the norm of the common parameter error.
-/
theorem floor_studentized_linear_bound
    {d h : EuclideanSpace ℝ (Fin 2)} {weight : ℝ}
    (hweight : 0 < weight) (hd : ‖d‖ ≤ weight) :
    |@inner ℝ _ _ d h| / weight ≤ ‖h‖ := by
  -- Apply the Cauchy-Schwarz inequality: |⟨d, h⟩| ≤ ‖d‖ * ‖h‖.
  have h_cauchy_schwarz : |inner ℝ d h| ≤ ‖d‖ * ‖h‖ := by
    exact abs_real_inner_le_norm d h;
  rw [ div_le_iff₀ ] <;> nlinarith [ norm_nonneg h ]

/-
A remainder controlled by the same positive floor remains controlled after
studentization.  This is the deterministic rate conversion needed before any
probabilistic `o_P` argument.
-/
theorem floor_studentized_remainder_bound
    {remainder weight epsilon : ℝ}
    (hweight : 0 < weight)
    (hrem : |remainder| ≤ epsilon * weight) :
    |remainder| / weight ≤ epsilon := by
  rwa [ div_le_iff₀ hweight ]

/-
Combining a linear term and a floor-controlled remainder gives the global
studentized bound used in the coverage proof.
-/
theorem floor_studentized_expansion_bound
    {d h : EuclideanSpace ℝ (Fin 2)} {remainder weight epsilon : ℝ}
    (hweight : 0 < weight) (hd : ‖d‖ ≤ weight)
    (hrem : |remainder| ≤ epsilon * weight) :
    |@inner ℝ _ _ d h + remainder| / weight ≤ ‖h‖ + epsilon := by
  have hLinear := floor_studentized_linear_bound (d := d) (h := h) hweight hd
  have hRemainder :=
    floor_studentized_remainder_bound hweight hrem
  calc
    |inner ℝ d h + remainder| / weight ≤
        (|inner ℝ d h| + |remainder|) / weight := by
          exact div_le_div_of_nonneg_right (abs_add_le _ _) (le_of_lt hweight)
    _ = |inner ℝ d h| / weight + |remainder| / weight := by ring
    _ ≤ ‖h‖ + epsilon := add_le_add hLinear hRemainder

end OperatorInterventions