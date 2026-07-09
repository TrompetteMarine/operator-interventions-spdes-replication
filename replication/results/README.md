# Generated results

All outputs are seeded and carry manifests (profile, package versions,
runtime, SHA-256 checksums).

- `tables/`, `figures/`, `logs/`: output of `make reproduce-standard`
  (250 replications per design; regenerated 2026-07-09 for this repository).
- `publication/`: publication-profile outputs of the end-to-end validation
  pipeline (1000 replications per design; estimation, uniform-target
  coverage, bootstrap sensitivity, Galerkin/temporal slopes,
  non-identification gaps; 19 figures + checksum manifests). Regenerate with
  `make reproduce-paper` (computationally heavy).
- `sweeps/`: additional experiments from `make sweeps`
  (`replication/scripts/extra_sweeps.py`): a finer N-grid estimation sweep
  on the design path n = 80 N^2 (standardised sd, bias, KS-normality
  p-values, empirical theta-sigma correlation) and the analytic
  post-intervention variance-monotonicity curves.

## A remark on the sweep

On the design path n = 80 N^2 the resolution parameter lambda_N * Delta_n is
held constant at pi^2/80 ~ 0.123. The sweep shows the standardised sds
hugging 1 and KS p-values fluctuating as expected, while the empirical
correlation corr(Z_theta, Z_sigma) stabilises around 0.23-0.29 instead of
vanishing: this is exactly the fixed-resolution artefact predicted by the
cross-information bound sqrt(lambda_N Delta_n / T) ~ 0.35 (see the
rate-separation remark in the paper). Asymptotic orthogonality requires
n / N^2 to diverge, not merely to stay large.
