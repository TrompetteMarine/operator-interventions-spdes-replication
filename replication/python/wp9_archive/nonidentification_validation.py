#!/usr/bin/env python3
"""WP8 non-identification counterexamples for operator-intervention SPDEs.

The script validates four exact constructions:

1. state-feedback gauge equivalence:
   two factual mechanisms generate the same OU law, but a common operator
   intervention produces different target laws;

2. open-loop exogenous forcing confounding:
   two scalar OU models have the same observed Gaussian law at the factual
   design point while retaining different forcing laws, so their common
   post-intervention laws differ;

3. unknown sensor calibration:
   the factual sensor process identifies c*sigma but not sigma, so field-level
   counterfactuals differ even though sensor-level counterfactuals remain equal;

4. cross-world coupling:
   identified counterfactual marginals do not identify the law of an individual
   contrast without a coupling convention.

It also verifies the finite-grid Gaussian forcing covariance construction.
"""
from __future__ import annotations

import argparse
import json
import math
import platform
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy.stats import norm


def ou_integrated_variance(rate: float, sigma: float, q: float, horizon: float) -> float:
    """Variance of integral_0^T X_t dt for dX=-rate*X dt+sigma*q dW, X0=0."""
    bracket = (
        horizon
        - 2.0 * (-math.expm1(-rate * horizon)) / rate
        + (-math.expm1(-2.0 * rate * horizon)) / (2.0 * rate)
    )
    return sigma * sigma * q * q * bracket / (rate * rate)


def ou_terminal_variance(rate: float, sigma: float, horizon: float) -> float:
    return sigma * sigma * (-math.expm1(-2.0 * rate * horizon)) / (2.0 * rate)


def gaussian_ks_zero_mean(v1: float, v2: float) -> float:
    scale = 8.0 * max(math.sqrt(v1), math.sqrt(v2))
    grid = np.linspace(-scale, scale, 250_001)
    return float(np.max(np.abs(norm.cdf(grid / math.sqrt(v1)) - norm.cdf(grid / math.sqrt(v2)))))


def gaussian_w2_zero_mean(v1: float, v2: float) -> float:
    return abs(math.sqrt(v1) - math.sqrt(v2))


def forcing_coefficient(rate: float, horizon: float) -> float:
    return -math.expm1(-rate * horizon) / rate


def unit_diffusion_variance(rate: float, horizon: float) -> float:
    return -math.expm1(-2.0 * rate * horizon) / (2.0 * rate)


def ou_noise_covariance(rate: float, sigma: float, times: np.ndarray) -> np.ndarray:
    t = times[:, None]
    s = times[None, :]
    return (
        sigma * sigma
        / (2.0 * rate)
        * (np.exp(-rate * np.abs(t - s)) - np.exp(-rate * (t + s)))
    )


def piecewise_forcing_matrix(rate: float, times: np.ndarray) -> np.ndarray:
    """Map piecewise-constant forcing amplitudes to states at grid times."""
    m = len(times)
    starts = np.concatenate(([0.0], times[:-1]))
    mat = np.zeros((m, m))
    for j in range(m):
        for ell in range(j + 1):
            delta = times[ell] - starts[ell]
            mat[j, ell] = (
                math.exp(-rate * (times[j] - times[ell]))
                * (-math.expm1(-rate * delta))
                / rate
            )
    return mat


def save_density_plot(
    path: Path,
    variances: list[float],
    labels: list[str],
    title: str,
    xlabel: str,
) -> None:
    max_sd = max(math.sqrt(v) for v in variances)
    x = np.linspace(-4.5 * max_sd, 4.5 * max_sd, 1600)
    plt.figure(figsize=(7.2, 4.4))
    for variance, label in zip(variances, labels):
        plt.plot(x, norm.pdf(x, scale=math.sqrt(variance)), label=label)
    plt.xlabel(xlabel)
    plt.ylabel("Density")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=220)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    rows: list[dict[str, float | str]] = []

    # ------------------------------------------------------------------
    # 1. Adapted state-feedback gauge construction
    # ------------------------------------------------------------------
    a0 = 1.0
    lam = 1.0
    gamma = 0.5
    a_tilde = 1.5
    sigma = 0.6
    q = 1.0
    horizon = 1.0

    factual_rate_1 = a0 * lam
    factual_rate_2_total = (a0 * lam + gamma) - gamma
    cf_rate_1 = a_tilde * lam
    cf_rate_2 = a_tilde * lam - gamma

    factual_v1 = ou_integrated_variance(factual_rate_1, sigma, q, horizon)
    factual_v2 = ou_integrated_variance(factual_rate_2_total, sigma, q, horizon)
    cf_v1 = ou_integrated_variance(cf_rate_1, sigma, q, horizon)
    cf_v2 = ou_integrated_variance(cf_rate_2, sigma, q, horizon)

    rows.append(
        {
            "construction": "adapted_feedback",
            "metric": "factual_variance_gap",
            "value": abs(factual_v1 - factual_v2),
        }
    )
    rows.append(
        {
            "construction": "adapted_feedback",
            "metric": "counterfactual_KS",
            "value": gaussian_ks_zero_mean(cf_v1, cf_v2),
        }
    )
    rows.append(
        {
            "construction": "adapted_feedback",
            "metric": "counterfactual_W2",
            "value": gaussian_w2_zero_mean(cf_v1, cf_v2),
        }
    )

    save_density_plot(
        out_dir / "wp8_adapted_factual_merge.png",
        [factual_v1, factual_v2],
        ["Mechanism 1", "Mechanism 2"],
        "Adapted forcing: factual laws merge exactly",
        r"$\int_0^T X_t\,dt$",
    )
    save_density_plot(
        out_dir / "wp8_adapted_counterfactual_split.png",
        [cf_v1, cf_v2],
        ["Mechanism 1 after intervention", "Mechanism 2 after intervention"],
        "Adapted forcing: common intervention separates the laws",
        r"$\int_0^T X_t^{\,do}\,dt$",
    )

    # ------------------------------------------------------------------
    # 2. Exogenous open-loop forcing at one observation time
    # ------------------------------------------------------------------
    a1 = 0.5
    a2 = 1.5
    a_cf = 1.0
    sigma_ex = 0.3
    obs_t = 1.0
    factual_target_variance = 0.5

    c1 = forcing_coefficient(a1, obs_t)
    c2 = forcing_coefficient(a2, obs_t)
    ccf = forcing_coefficient(a_cf, obs_t)
    h1 = unit_diffusion_variance(a1, obs_t)
    h2 = unit_diffusion_variance(a2, obs_t)
    hcf = unit_diffusion_variance(a_cf, obs_t)

    tau1_sq = (factual_target_variance - sigma_ex**2 * h1) / (c1 * c1)
    tau2_sq = (factual_target_variance - sigma_ex**2 * h2) / (c2 * c2)
    ex_factual_v1 = tau1_sq * c1 * c1 + sigma_ex**2 * h1
    ex_factual_v2 = tau2_sq * c2 * c2 + sigma_ex**2 * h2
    ex_cf_v1 = tau1_sq * ccf * ccf + sigma_ex**2 * hcf
    ex_cf_v2 = tau2_sq * ccf * ccf + sigma_ex**2 * hcf

    rows.extend(
        [
            {
                "construction": "exogenous_one_time",
                "metric": "forcing_variance_model_1",
                "value": tau1_sq,
            },
            {
                "construction": "exogenous_one_time",
                "metric": "forcing_variance_model_2",
                "value": tau2_sq,
            },
            {
                "construction": "exogenous_one_time",
                "metric": "factual_variance_gap",
                "value": abs(ex_factual_v1 - ex_factual_v2),
            },
            {
                "construction": "exogenous_one_time",
                "metric": "counterfactual_KS",
                "value": gaussian_ks_zero_mean(ex_cf_v1, ex_cf_v2),
            },
            {
                "construction": "exogenous_one_time",
                "metric": "counterfactual_W2",
                "value": gaussian_w2_zero_mean(ex_cf_v1, ex_cf_v2),
            },
        ]
    )

    save_density_plot(
        out_dir / "wp8_exogenous_factual_merge.png",
        [ex_factual_v1, ex_factual_v2],
        ["Operator $a_1$ + forcing law 1", "Operator $a_2$ + forcing law 2"],
        "Open-loop forcing: identical factual observation law",
        r"$X_T$",
    )
    save_density_plot(
        out_dir / "wp8_exogenous_counterfactual_split.png",
        [ex_cf_v1, ex_cf_v2],
        ["Model 1 after common intervention", "Model 2 after common intervention"],
        "Open-loop forcing: post-intervention laws separate",
        r"$X_T^{\,do}$",
    )

    # ------------------------------------------------------------------
    # 2b. Any finite grid: covariance factor construction
    # ------------------------------------------------------------------
    times = np.asarray([0.25, 0.5, 0.75, 1.0])
    l1 = piecewise_forcing_matrix(a1, times)
    l2 = piecewise_forcing_matrix(a2, times)
    lcf = piecewise_forcing_matrix(a_cf, times)
    cw1 = ou_noise_covariance(a1, sigma_ex, times)
    cw2 = ou_noise_covariance(a2, sigma_ex, times)
    cwcf = ou_noise_covariance(a_cf, sigma_ex, times)

    target_scale = max(np.linalg.eigvalsh(cw1).max(), np.linalg.eigvalsh(cw2).max()) + 0.8
    target_cov = target_scale * np.eye(len(times))
    k1 = np.linalg.solve(l1, target_cov - cw1)
    k1 = np.linalg.solve(l1, k1.T).T
    k2 = np.linalg.solve(l2, target_cov - cw2)
    k2 = np.linalg.solve(l2, k2.T).T
    k1 = 0.5 * (k1 + k1.T)
    k2 = 0.5 * (k2 + k2.T)

    factual_cov1 = l1 @ k1 @ l1.T + cw1
    factual_cov2 = l2 @ k2 @ l2.T + cw2
    cf_cov1 = lcf @ k1 @ lcf.T + cwcf
    cf_cov2 = lcf @ k2 @ lcf.T + cwcf

    rows.extend(
        [
            {
                "construction": "exogenous_finite_grid",
                "metric": "minimum_eigenvalue_K1",
                "value": float(np.linalg.eigvalsh(k1).min()),
            },
            {
                "construction": "exogenous_finite_grid",
                "metric": "minimum_eigenvalue_K2",
                "value": float(np.linalg.eigvalsh(k2).min()),
            },
            {
                "construction": "exogenous_finite_grid",
                "metric": "factual_covariance_frobenius_gap",
                "value": float(np.linalg.norm(factual_cov1 - factual_cov2, ord="fro")),
            },
            {
                "construction": "exogenous_finite_grid",
                "metric": "counterfactual_covariance_frobenius_gap",
                "value": float(np.linalg.norm(cf_cov1 - cf_cov2, ord="fro")),
            },
        ]
    )

    # ------------------------------------------------------------------
    # 3. Unknown calibration
    # ------------------------------------------------------------------
    theta = 0.7
    theta_cf = 0.3
    c_sensor_1, sigma_1 = 1.0, 0.8
    c_sensor_2, sigma_2 = 2.0, 0.4
    observed_factual_v1 = ou_terminal_variance(theta, c_sensor_1 * sigma_1, horizon)
    observed_factual_v2 = ou_terminal_variance(theta, c_sensor_2 * sigma_2, horizon)
    field_cf_v1 = ou_terminal_variance(theta_cf, sigma_1, horizon)
    field_cf_v2 = ou_terminal_variance(theta_cf, sigma_2, horizon)
    sensor_cf_v1 = ou_terminal_variance(theta_cf, c_sensor_1 * sigma_1, horizon)
    sensor_cf_v2 = ou_terminal_variance(theta_cf, c_sensor_2 * sigma_2, horizon)

    rows.extend(
        [
            {
                "construction": "unknown_calibration",
                "metric": "factual_sensor_variance_gap",
                "value": abs(observed_factual_v1 - observed_factual_v2),
            },
            {
                "construction": "unknown_calibration",
                "metric": "field_counterfactual_KS",
                "value": gaussian_ks_zero_mean(field_cf_v1, field_cf_v2),
            },
            {
                "construction": "unknown_calibration",
                "metric": "sensor_counterfactual_variance_gap",
                "value": abs(sensor_cf_v1 - sensor_cf_v2),
            },
        ]
    )

    save_density_plot(
        out_dir / "wp8_calibration_field_counterfactual.png",
        [field_cf_v1, field_cf_v2],
        ["$(c,\\sigma)=(1,0.8)$", "$(c,\\sigma)=(2,0.4)$"],
        "Unknown calibration: field counterfactual is not identified",
        r"$X_T^{\,do}$",
    )
    save_density_plot(
        out_dir / "wp8_calibration_sensor_counterfactual.png",
        [sensor_cf_v1, sensor_cf_v2],
        ["Sensor mechanism 1", "Sensor mechanism 2"],
        "Invariant calibration: sensor-level counterfactual remains identified",
        r"$Y_T^{\,do}$",
    )

    # ------------------------------------------------------------------
    # 4. Cross-world coupling
    # ------------------------------------------------------------------
    v_a, v_b = 0.3, 0.7
    correlations = [0.0, 0.8, -0.5]
    effect_variances = [
        v_a + v_b - 2.0 * rho * math.sqrt(v_a * v_b) for rho in correlations
    ]
    save_density_plot(
        out_dir / "wp8_crossworld_coupling.png",
        effect_variances,
        [f"$\\rho={rho:g}$" for rho in correlations],
        "Same counterfactual marginals, different unit-level effect laws",
        r"$X^{a}-X^{b}$",
    )
    for rho, variance in zip(correlations, effect_variances):
        rows.append(
            {
                "construction": "crossworld_coupling",
                "metric": f"effect_variance_rho_{rho:g}",
                "value": variance,
            }
        )

    # ------------------------------------------------------------------
    # 5. Factual merge / counterfactual split schematic
    # ------------------------------------------------------------------
    plt.figure(figsize=(8.2, 4.5))
    ax = plt.gca()
    ax.axis("off")
    nodes = {
        "m1": (0.08, 0.72, "Mechanism 1\n$(A_1,G_1)$"),
        "m2": (0.08, 0.28, "Mechanism 2\n$(A_2,G_2)$"),
        "fact": (0.48, 0.50, "Same factual\nobserved law"),
        "cf1": (0.88, 0.72, "Counterfactual law 1"),
        "cf2": (0.88, 0.28, "Counterfactual law 2"),
    }
    for _, (x, y, label) in nodes.items():
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            bbox={"boxstyle": "round,pad=0.45", "facecolor": "white", "edgecolor": "black"},
            transform=ax.transAxes,
        )
    arrow = {"arrowstyle": "->", "linewidth": 1.5}
    ax.annotate("", xy=(0.39, 0.53), xytext=(0.17, 0.70), xycoords="axes fraction", arrowprops=arrow)
    ax.annotate("", xy=(0.39, 0.47), xytext=(0.17, 0.30), xycoords="axes fraction", arrowprops=arrow)
    ax.annotate("", xy=(0.79, 0.70), xytext=(0.57, 0.53), xycoords="axes fraction", arrowprops=arrow)
    ax.annotate("", xy=(0.79, 0.30), xytext=(0.57, 0.47), xycoords="axes fraction", arrowprops=arrow)
    ax.text(0.68, 0.55, "same declared\noperator intervention", ha="center", va="bottom", transform=ax.transAxes)
    ax.text(0.48, 0.08, "Factual merging does not imply counterfactual merging", ha="center", transform=ax.transAxes)
    plt.tight_layout()
    plt.savefig(out_dir / "wp8_factual_merge_counterfactual_split_diagram.png", dpi=220)
    plt.close()

    frame = pd.DataFrame(rows)
    frame.to_csv(out_dir / "wp8_nonidentification_summary.csv", index=False)

    runtime = {
        "elapsed_seconds": time.perf_counter() - start,
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pandas": pd.__version__,
        "parameters": {
            "adapted": {
                "a0": a0,
                "gamma": gamma,
                "a_tilde": a_tilde,
                "sigma": sigma,
                "T": horizon,
            },
            "exogenous": {
                "a1": a1,
                "a2": a2,
                "a_tilde": a_cf,
                "sigma": sigma_ex,
                "target_factual_variance": factual_target_variance,
            },
            "calibration": {
                "theta": theta,
                "theta_tilde": theta_cf,
                "c1": c_sensor_1,
                "sigma1": sigma_1,
                "c2": c_sensor_2,
                "sigma2": sigma_2,
            },
        },
    }
    (out_dir / "wp8_runtime_diagnostics.json").write_text(
        json.dumps(runtime, indent=2), encoding="utf-8"
    )

    print(frame.to_string(index=False, float_format=lambda x: f"{x:.10g}"))


if __name__ == "__main__":
    main()
