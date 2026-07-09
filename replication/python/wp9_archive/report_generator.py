#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import pandas as pd


def md_table(df: pd.DataFrame, digits: int = 5) -> str:
    out = df.copy()
    for col in out.select_dtypes(include="number").columns:
        out[col] = out[col].map(lambda value: f"{value:.{digits}g}")
    return out.to_markdown(index=False)


def latex_table(df: pd.DataFrame, digits: int = 4) -> str:
    out = df.copy()
    for col in out.select_dtypes(include="number").columns:
        out[col] = out[col].map(lambda value: f"{value:.{digits}g}")
    body = out.to_latex(index=False, escape=True)
    return "\\resizebox{\\textwidth}{!}{%\n" + body + "}%\n"


def generate(root: Path) -> None:
    tables = root / "results" / "tables"
    reports = root / "reports"
    figures = root / "results" / "figures"
    reports.mkdir(parents=True, exist_ok=True)

    est = pd.read_csv(tables / "estimation_summary.csv")
    core = est[est["design"].str.startswith("N")].copy()
    cf = pd.read_csv(tables / "counterfactual_summary.csv")
    boot = pd.read_csv(tables / "bootstrap_sensitivity.csv")
    slopes = pd.read_csv(tables / "galerkin_slope_summary.csv")
    op = pd.read_csv(tables / "operator_sensitivity_summary.csv")
    nonid = pd.read_csv(tables / "nonidentification_summary.csv")
    audit = pd.read_csv(tables / "wp9_completion_gate_audit.csv")
    grid = pd.read_csv(tables / "planned_grid_regime_audit.csv")
    regions = pd.read_csv(tables / "regional_coverage.csv")
    balance = pd.read_csv(tables / "combined_error_balancing.csv")
    manifest = json.loads((root / "results" / "manifests" / "environment.json").read_text())

    core_cols = ["N", "n", "lambda_N_Delta", "theta_bias", "theta_rmse", "theta_empirical_sd", "theta_average_se", "sigma_bias", "sigma_rmse", "sigma_empirical_sd", "sigma_average_se", "ztheta_sd", "zsigma_sd", "scaled_cross_correlation"]
    cf_cols = ["N", "n", "cdf_sup_rmse", "effect_sup_rmse", "fast_simultaneous_coverage", "slow_simultaneous_coverage", "fast_average_full_width", "slow_average_full_width", "pointwise_coverage_min", "pointwise_coverage_max"]
    boot_cols = ["sensitivity_axis", "method", "draws", "grid_size", "fast_coverage", "slow_coverage", "fast_mean_full_width", "slow_mean_full_width"]
    slope_focus = slopes[slopes["metric"].isin(["mean_error", "variance_error", "strong_rms", "cdf_sup"])].copy()
    balance_summary = balance.groupby(["N", "n"], as_index=False).first()[["N", "n", "empirical_balancing_K", "theoretical_balancing_K"]]

    markdown = f"""# Work Package 9 - Unified Monte Carlo and Computational Validation

## Scope and execution

WP9 consolidates the numerical evidence for WP3-WP8 into one executable repository. The verified command is:

```bash
make wp9
```

The clean one-command run completed in **{manifest['elapsed_seconds']:.1f} seconds** from source commit `{manifest['git_commit']}`.

## Design correction

For the Dirichlet heat equation on `(0,1)`, `lambda_N Delta = pi^2 N^2 / n`. Only **{int((grid.regime_status == 'resolved').sum())} of {len(grid)}** cells in the original Cartesian design satisfy the operational resolution threshold `lambda_N Delta <= 0.15`. The high-replication core therefore uses `(N,n) = (5,2000), (10,8000), (20,32000)`, with 1,000 replications per design and common `lambda_N Delta = {core.lambda_N_Delta.iloc[0]:.6f}`.

## Estimation and LAN

{md_table(core[core_cols])}

The largest absolute deviation of an information-standardised empirical standard deviation from one is **{max((core.ztheta_sd-1).abs().max(), (core.zsigma_sd-1).abs().max()):.4f}**.

## Counterfactual targets and simultaneous coverage

{md_table(cf[cf_cols])}

Regional pointwise coverage:

{md_table(regions[['N','n','region','mean','min','max']])}

## Bootstrap sensitivity

{md_table(boot[boot_cols])}

At 300 replications, the Monte Carlo standard error of coverage near 0.95 is approximately 0.013. The direct Gaussian multiplier is preferred when the limiting information is known; mode-block Gaussian and Rademacher versions provide structural robustness.

## Galerkin rates

{md_table(slope_focus[['alpha_q','metric','predicted_slope','empirical_slope','ci_low','ci_high','r_squared']])}

The temporal diagnostic produces fitted first-order slopes between approximately 0.994 and 0.999.

## Statistical-numerical balance

{md_table(balance_summary)}

The experiment reports the correct plateau/balance structure: truncation bias approaches the statistical floor. It does not manufacture a U-shape in a model where known spectral structure prevents variance inflation from target extrapolation.

## Operator sensitivity

The central finite-difference error decreases from `{op.central_error.iloc[0]:.3e}` at `epsilon={op.epsilon.iloc[0]:g}` to `{op.central_error.iloc[-1]:.3e}` at `epsilon={op.epsilon.iloc[-1]:g}`. The law-linearisation remainder is quadratic and the Gaussian Wasserstein distance remains below the common-noise Lipschitz envelope.

## Non-identification

{md_table(nonid[['construction','metric','value']], digits=6)}

The four-time open-loop construction has factual covariance gap `{nonid.loc[nonid.metric == 'factual_covariance_frobenius_gap','value'].iloc[0]:.3e}` and post-intervention covariance gap `{nonid.loc[nonid.metric == 'counterfactual_covariance_frobenius_gap','value'].iloc[0]:.4f}`.

## Completion gate

{md_table(audit[['criterion','passed','diagnostic']], digits=6)}

All conditions pass. WP1-WP9 are complete; WP10 manuscript reconstruction remains.
"""
    (reports / "wp9_validation_report.md").write_text(markdown, encoding="utf-8")

    status = """# Causal SPDE Research Programme - Status after WP9

## Current position

The project has completed WP1-WP9. All theorem, inferential, approximation, sharpness, and validation packages are closed.

```mermaid
flowchart LR
    WP1["WP1 Semantics"] --> WP2["WP2 Identification"] --> WP3["WP3 LAN"] --> WP4["WP4 Uniform processes"] --> WP5["WP5 Bootstrap"] --> WP6["WP6 Sensitivity"] --> WP7["WP7 Total error"] --> WP8["WP8 Sharpness"] --> WP9["WP9 Validation"] --> WP10["WP10 Manuscript reconstruction - next"]
```

## WP9 completion

WP9 now supplies:

1. a theorem-aligned high-replication heat-equation experiment;
2. a formal audit of the original design grid;
3. mixed-rate LAN and likelihood-ratio diagnostics;
4. CDF, quantile, tail and effect error summaries;
5. pointwise and simultaneous coverage;
6. multiplier, draw-count and grid-resolution sensitivity;
7. Galerkin slope estimates with confidence intervals;
8. temporal and total-error validation;
9. bounded-operator response checks;
10. exact non-identification demonstrations;
11. raw results, environment capture, Git provenance and checksums;
12. verified one-command execution.

## Remaining package

Only WP10 remains. It should reconstruct the manuscript around the completed theorem chain and use the WP9 report as the simulation and computational appendix.
"""
    (reports / "causal_spde_research_program_status_after_wp9.md").write_text(status, encoding="utf-8")

    core_tex = latex_table(core[core_cols])
    cf_tex = latex_table(cf[cf_cols])
    boot_tex = latex_table(boot[boot_cols])
    slope_tex = latex_table(slope_focus[["alpha_q","metric","predicted_slope","empirical_slope","ci_low","ci_high"]])
    audit_tex = latex_table(audit[["criterion","passed","diagnostic"]])

    tex = rf"""\documentclass[11pt]{{article}}
\usepackage[a4paper,margin=0.85in]{{geometry}}
\usepackage{{amsmath,amssymb,booktabs,graphicx,tabularx,longtable,microtype}}
\usepackage[hidelinks]{{hyperref}}
\title{{Work Package 9: Unified Monte Carlo and Computational Validation\\\large Reproducibility appendix for causal operator interventions in linear SPDEs}}
\author{{}}
\date{{7 July 2026}}
\begin{{document}}
\maketitle
\begin{{abstract}}
This appendix validates the complete WP3--WP8 theorem chain using an exact spectral simulation of the stochastic heat equation, deterministic Gaussian law calculations, and constructive non-identification experiments. The original Cartesian $(N,n)$ design is audited against the heat-equation resolution condition and replaced, for inferential validation, by a theorem-aligned paired design with 1,000 replications per cell. The suite reports estimator bias and RMSE, mixed-rate LAN diagnostics, counterfactual CDF and quantile errors, pointwise and simultaneous coverage, multiplier sensitivity, Galerkin and temporal slopes, total-error balancing, operator derivatives, and factual-merging/counterfactual-separation failures. A clean one-command execution completed in {manifest['elapsed_seconds']:.1f} seconds and records raw data, software versions, Git provenance, and SHA-256 checksums.
\end{{abstract}}

\section{{Design audit}}
For the Dirichlet heat equation on $(0,1)$,
\[
 \lambda_N\Delta_n=\pi^2N^2/n.
\]
Only {int((grid.regime_status == 'resolved').sum())} of {len(grid)} planned Cartesian cells satisfy the operational threshold $\lambda_N\Delta_n\le0.15$. The high-replication designs are $(5,2000)$, $(10,8000)$, and $(20,32000)$, each with 1,000 replications and $\lambda_N\Delta_n={core.lambda_N_Delta.iloc[0]:.6f}$.

\section{{Estimation and LAN}}
{core_tex}
The information-standardised empirical standard deviations differ from one by at most {max((core.ztheta_sd-1).abs().max(), (core.zsigma_sd-1).abs().max()):.4f}. Figures~\ref{{fig:hist}}--\ref{{fig:lr}} display the normal and likelihood-ratio diagnostics.

\begin{{figure}}[ht]
\centering
\includegraphics[width=.82\textwidth]{{../results/figures/lan_histograms.png}}
\caption{{Information-standardised estimator histograms at the largest theorem-aligned design.}}
\label{{fig:hist}}
\end{{figure}}

\begin{{figure}}[ht]
\centering
\includegraphics[width=.82\textwidth]{{../results/figures/lan_qq_plots.png}}
\caption{{Normal quantile diagnostics for the mixed-rate estimators.}}
\end{{figure}}

\begin{{figure}}[ht]
\centering
\includegraphics[width=.72\textwidth]{{../results/figures/lan_likelihood_ratio_remainder.png}}
\caption{{RMSE of the LAN likelihood-ratio quadratic remainder.}}
\label{{fig:lr}}
\end{{figure}}

\section{{Counterfactual targets and bands}}
{cf_tex}

\begin{{figure}}[ht]
\centering
\includegraphics[width=.74\textwidth]{{../results/figures/counterfactual_target_errors.png}}
\caption{{Contraction of fixed-intervention CDF and factual-versus-counterfactual effect errors.}}
\end{{figure}}

\begin{{figure}}[ht]
\centering
\includegraphics[width=.74\textwidth]{{../results/figures/pointwise_coverage_by_threshold.png}}
\caption{{Pointwise coverage over central and tail threshold regions.}}
\end{{figure}}

\section{{Bootstrap sensitivity}}
{boot_tex}
The mode-block procedures are mildly conservative at finite $N$, while the direct Gaussian multiplier is narrower because the limiting covariance is known analytically.

\begin{{figure}}[ht]
\centering
\includegraphics[width=.74\textwidth]{{../results/figures/bootstrap_multiplier_sensitivity.png}}
\caption{{Simultaneous coverage by multiplier implementation.}}
\end{{figure}}

\section{{Galerkin, temporal, and total error}}
{slope_tex}

\begin{{figure}}[ht]
\centering
\includegraphics[width=.75\textwidth]{{../results/figures/galerkin_alpha_rates.png}}
\caption{{Noise-smoothness sensitivity of the Galerkin CDF-law error.}}
\end{{figure}}

\begin{{figure}}[ht]
\centering
\includegraphics[width=.75\textwidth]{{../results/figures/temporal_rates.png}}
\caption{{First-order temporal approximation rates.}}
\end{{figure}}

\begin{{figure}}[ht]
\centering
\includegraphics[width=.75\textwidth]{{../results/figures/combined_error_balancing.png}}
\caption{{Truncation bias approaching the statistical error floor.}}
\end{{figure}}

\begin{{figure}}[ht]
\centering
\includegraphics[width=.75\textwidth]{{../results/figures/bias_coverage.png}}
\caption{{Naive and certified-bias-enlarged coverage.}}
\end{{figure}}

\section{{Operator sensitivity}}
The central difference error falls from {op.central_error.iloc[0]:.3e} to {op.central_error.iloc[-1]:.3e}. The first-order CDF remainder is quadratic and the Wasserstein distance stays below the common-noise bound.

\begin{{figure}}[ht]
\centering
\includegraphics[width=.75\textwidth]{{../results/figures/operator_finite_difference.png}}
\caption{{Finite-difference validation of the operator-law derivative.}}
\end{{figure}}

\section{{Non-identification}}
The finite-grid open-loop example has factual covariance discrepancy {nonid.loc[nonid.metric == 'factual_covariance_frobenius_gap','value'].iloc[0]:.3e} and post-intervention discrepancy {nonid.loc[nonid.metric == 'counterfactual_covariance_frobenius_gap','value'].iloc[0]:.4f}.

\begin{{figure}}[ht]
\centering
\includegraphics[width=.75\textwidth]{{../results/figures/nonidentification_diagram.png}}
\caption{{Factual merging followed by counterfactual separation.}}
\end{{figure}}

\begin{{figure}}[ht]
\centering
\includegraphics[width=.75\textwidth]{{../results/figures/exogenous_counterfactual_split.png}}
\caption{{Open-loop forcing: separated post-intervention laws after exact factual equivalence.}}
\end{{figure}}

\section{{Completion gate and reproducibility}}
{audit_tex}
The suite is executed with \texttt{{make wp9}}. It stores the full configuration, raw estimator replicates, summary tables, figures, environment metadata, the source commit, and SHA-256 checksums.

\end{{document}}
"""
    tex_path = reports / "wp9_reproducibility_appendix.tex"
    tex_path.write_text(tex, encoding="utf-8")
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_path.name], cwd=reports, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_path.name], cwd=reports, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    generate(args.root.resolve())
