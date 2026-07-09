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
  paper_merged.tex        master (draft build: verification flags visible)
  build_supplement.py     assembles the proofs section from part sources
  sections/ closures/ figures*/ wp_src/   content
  pdf/                    compiled PDFs (draft + submission)
replication/
  python/         reference implementation (causal_spdes package + tests)
  config/         deterministic simulation profiles (seeded)
  validation/     end-to-end validation pipeline (generates paper figures)
  results/        generated tables, figures, logs, manifests
  scripts/        additional experiment sweeps
```

## Build the paper

```bash
cd paper
python3 build_supplement.py
pdflatex paper_merged && bibtex paper_merged && pdflatex paper_merged && pdflatex paper_merged
# submission build (no draft flags):
pdflatex -jobname=paper_submission "\def\SUBMISSIONCLEAN{}\input{paper_merged}"
```

## Reproduce the numerics

```bash
pip install -e .[dev]
make verify              # unit tests: exact identities, formula parity
make reproduce-standard  # medium Monte Carlo profile (seeded)
make reproduce-paper     # full validation pipeline -> paper figures
make sweeps              # additional experiment sweeps (results/sweeps)
```

All randomness is seeded; runs write manifests (profile, versions, runtime,
SHA-256 checksums) alongside outputs.

## Licences

Code: MIT (`LICENSE`). Manuscript text and figures: CC BY 4.0
(`LICENSE-TEXT`).
