# Operator Interventions in Linear SPDEs

Manuscript and replication package for

> **Operator Interventions in Linear SPDEs: Galerkin Structural Semantics,
> Mixed-Rate Local Asymptotic Normality, and Uniform Inference for
> Post-Intervention Laws** — G. L. S. Bontemps, working paper, 2026.

The paper develops a causal-statistical theory for interventions that
replace the generator coefficient of a linear parabolic SPDE: structural
semantics as the common-noise limit of intervened Galerkin models, exact
and target-specific identification, mixed-rate local asymptotic normality
under exact discrete spectral observation (drift at sqrt(Lambda_N), scale at
sqrt(Nn)), uniform post-intervention CDF/quantile/tail/effect processes with
feasible multiplier bands and contact-set tests, operator-to-law derivatives,
a combined statistical–numerical error theorem, and sharp non-identification
constructions.

## Layout

```
paper/            LaTeX sources (single-document manuscript)
  paper_merged.tex        master
  build_supplement.py     assembles the proofs section from part sources
  sections/ closures/ figures*/ wp_src/   content
  pdf/                    compiled PDFs (draft + submission)
replication/
  python/         reference implementation (causal_spdes package + tests)
  config/         deterministic simulation profiles (seeded)
  validation/     end-to-end validation pipeline (generates paper figures)
  results/        generated tables, figures, logs, manifests
  scripts/        additional experiment sweeps (incl. regime_scan.py)
formalization/    Lean 4 / Mathlib formalization archive and audit reports
  RequestProject/ machine-checked finite-dimensional cores of the proofs
  *_AUDIT.md      audit reports mapping Lean declarations to the paper's
                  numbered statements (basis of the v3 proof corrections;
                  see paper/CHANGES_AUDIT_v3.md)
  FORMALISATION_STATUS.md  component-level status table
                  (KERNEL_CHECKED / PARTIALLY_FORMALISED / PAPER_PROOF_ONLY /
                   EXTERNAL_THEOREM / NUMERICALLY_TESTED)
```

`paper/theorem_registry.md` is the single source of truth for statement
signatures: model namespace, hypotheses, proof location, Lean components,
and status for every numbered main-text result.

## Build the paper

```bash
cd paper
python3 build_supplement.py
pdflatex paper_merged && bibtex paper_merged && pdflatex paper_merged && pdflatex paper_merged
# submission build (no draft flags):
pdflatex -jobname=paper_submission "\def\SUBMISSIONCLEAN{}\input{paper_merged}"
```

## Reproduce the numerics 

first, create a python venv e.g. , by running something like :

```bash
python3 -m venv .venv
source .venv/bin/activate
```
Ensure pytest is installed properly by running :

```bash
pip install pytest
```

Then, install the replication package 

```bash
pip install -e .[dev]    # if it doesn't land properly, just run `pip install -e .`
make verify              # unit tests: exact identities, formula parity
make reproduce-standard  # medium Monte Carlo profile (seeded)
make reproduce-paper     # full validation pipeline -> paper figures
make sweeps              # additional experiment sweeps (results/sweeps)
```

All randomness is seeded; runs write manifests (profile, versions, runtime,
SHA-256 checksums) alongside outputs.

The regime scan distinguishing asymptotically aligned designs
(n/N^2 diverging) from fixed-resolution and deliberately under-resolved
designs is run by

```bash
python3 replication/scripts/regime_scan.py   # writes results/tables/regime_scan.csv
```

## Check the formalization

```bash
cd formalization
lake build    # requires the pinned Lean toolchain (lean-toolchain) + Mathlib
```

The audit reports in `formalization/` record which statements are
machine-checked, the two corrections implemented in the manuscript
(constrained profile MLE; explicit spectral-growth hypothesis), and the
dependencies that remain classical imports (Part S0 of the paper).

## Licences

Code: MIT (`LICENSE`). Manuscript text and figures: CC BY 4.0
(`LICENSE-TEXT`).
