# WP9 - Unified Monte Carlo and Reproducibility Suite

This repository validates the theorem chain for **Operator Interventions, Identification, and Uniform Counterfactual Inference for Linear SPDEs**.

## One-command execution

```bash
make wp9
```

or

```bash
python run_wp9.py --config config/wp9_paper.json
```

The command produces raw replicate data, summary tables, figures, environment metadata, a Git commit identifier, and SHA-256 checksums under `results/`.

## Validation blocks

1. Exact spectral OU likelihood, mixed-rate LAN, MLE bias/RMSE and likelihood-ratio expansion.
2. Counterfactual CDF, quantile, tail and distributional-effect errors.
3. Pointwise and simultaneous coverage, including multiplier distribution, draw-count and grid-resolution sensitivity.
4. Galerkin and temporal rates, slope confidence intervals and statistical-numerical balancing.
5. Non-commuting operator sensitivity and Wasserstein bounds.
6. Adapted and open-loop non-identification counterexamples.

## Design correction

The planned Cartesian grid is audited but not mislabelled as asymptotic evidence. For the heat equation on `(0,1)`,

```text
lambda_N * Delta = pi^2 N^2 / n.
```

The high-replication core therefore uses `n = 80 N^2`, which keeps this quantity at approximately `0.1234`.
