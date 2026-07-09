#!/usr/bin/env python3
"""WP6 operator-sensitivity validation for a non-commuting perturbation.

The script computes the exact finite-dimensional Gaussian field-functional law
under A + epsilon B, the analytic sensitivity at epsilon=0, finite-difference
approximations, the first-order CDF remainder, and a common-noise W2 envelope.
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
from numpy.linalg import eigvalsh, norm
from scipy.integrate import solve_ivp
from scipy.stats import norm as gaussian


def build_model() -> dict[str, object]:
    dimension = 6
    A = -np.diag(np.array([1.0, 2.0, 4.0, 7.0, 11.0, 16.0]))
    B = np.zeros((dimension, dimension))
    for index in range(dimension):
        B[index, index] = 0.15 * ((-1.0) ** index)
    for index in range(dimension - 1):
        value = 0.28 / ((index + 1.0) ** 0.2)
        B[index, index + 1] = value
        B[index + 1, index] = value
    G = np.diag(np.array([1.0, 0.85, 0.70, 0.55, 0.45, 0.35]))
    u0 = np.array([0.80, -0.35, 0.20, 0.12, -0.08, 0.05])
    return {
        "dimension": dimension,
        "A": A,
        "B": B,
        "G": G,
        "u0": u0,
        "sigma": 0.70,
        "horizon": 1.50,
    }


def weight(t: float, horizon: float) -> np.ndarray:
    vector_1 = np.array([0.60, -0.40, 0.30, 0.20, -0.10, 0.08])
    vector_2 = np.array([0.20, 0.30, -0.25, 0.10, 0.15, -0.05])
    return np.exp(-0.35 * t) * vector_1 + np.sin(np.pi * t / horizon) * vector_2


def compute_law(
    epsilon: float,
    model: dict[str, object],
    t_grid: np.ndarray,
    with_sensitivity: bool = False,
) -> tuple[float, ...]:
    A = np.asarray(model["A"])
    B = np.asarray(model["B"])
    G = np.asarray(model["G"])
    u0 = np.asarray(model["u0"])
    sigma = float(model["sigma"])
    horizon = float(model["horizon"])
    dimension = int(model["dimension"])
    perturbed = A + epsilon * B
    weights = np.asarray([weight(t, horizon) for t in t_grid])

    if with_sensitivity:
        def forward_rhs(t: float, state: np.ndarray) -> np.ndarray:
            x = state[:dimension]
            y = state[dimension:]
            return np.concatenate((perturbed @ x, perturbed @ y + B @ x))

        forward = solve_ivp(
            forward_rhs,
            (0.0, horizon),
            np.concatenate((u0, np.zeros(dimension))),
            t_eval=t_grid,
            rtol=1.0e-10,
            atol=1.0e-12,
        )
        if not forward.success:
            raise RuntimeError(forward.message)
        x = forward.y[:dimension].T
        y = forward.y[dimension:].T
    else:
        forward = solve_ivp(
            lambda _t, x: perturbed @ x,
            (0.0, horizon),
            u0,
            t_eval=t_grid,
            rtol=1.0e-10,
            atol=1.0e-12,
        )
        if not forward.success:
            raise RuntimeError(forward.message)
        x = forward.y.T
        y = None

    reverse_grid = t_grid[::-1]
    if with_sensitivity:
        def backward_rhs(t: float, state: np.ndarray) -> np.ndarray:
            g = state[:dimension]
            h = state[dimension:]
            return np.concatenate(
                (-weight(t, horizon) - perturbed.T @ g, -B.T @ g - perturbed.T @ h)
            )

        backward = solve_ivp(
            backward_rhs,
            (horizon, 0.0),
            np.zeros(2 * dimension),
            t_eval=reverse_grid,
            rtol=1.0e-10,
            atol=1.0e-12,
        )
        if not backward.success:
            raise RuntimeError(backward.message)
        g = backward.y[:dimension].T[::-1]
        h = backward.y[dimension:].T[::-1]
    else:
        backward = solve_ivp(
            lambda t, g: -weight(t, horizon) - perturbed.T @ g,
            (horizon, 0.0),
            np.zeros(dimension),
            t_eval=reverse_grid,
            rtol=1.0e-10,
            atol=1.0e-12,
        )
        if not backward.success:
            raise RuntimeError(backward.message)
        g = backward.y.T[::-1]
        h = None

    mean = float(np.trapezoid(np.sum(weights * x, axis=1), t_grid))
    transferred = g @ G
    variance = float(sigma**2 * np.trapezoid(np.sum(transferred**2, axis=1), t_grid))

    if not with_sensitivity:
        return mean, variance

    mean_derivative = float(np.trapezoid(np.sum(weights * y, axis=1), t_grid))
    transfer_derivative = h @ G
    variance_derivative = float(
        2.0
        * sigma**2
        * np.trapezoid(np.sum(transferred * transfer_derivative, axis=1), t_grid)
    )
    return mean, variance, mean_derivative, variance_derivative


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    model = build_model()
    horizon = float(model["horizon"])
    t_grid = np.linspace(0.0, horizon, 1201)

    mean_0, variance_0, mean_dot, variance_dot = compute_law(
        0.0, model, t_grid, with_sensitivity=True
    )
    sd_0 = math.sqrt(variance_0)
    threshold = mean_0 + 0.30 * sd_0
    standardised = (threshold - mean_0) / sd_0
    cdf_0 = float(gaussian.cdf(standardised))
    cdf_dot = float(
        gaussian.pdf(standardised)
        * (
            -mean_dot / sd_0
            - (threshold - mean_0) * variance_dot / (2.0 * variance_0 ** 1.5)
        )
    )

    epsilons = np.asarray([0.100, 0.050, 0.020, 0.010, 0.005, 0.002])
    rows: list[dict[str, float]] = []
    for epsilon in epsilons:
        mean_plus, variance_plus = compute_law(epsilon, model, t_grid)
        mean_minus, variance_minus = compute_law(-epsilon, model, t_grid)
        cdf_plus = float(
            gaussian.cdf((threshold - mean_plus) / math.sqrt(variance_plus))
        )
        cdf_minus = float(
            gaussian.cdf((threshold - mean_minus) / math.sqrt(variance_minus))
        )
        forward_difference = (cdf_plus - cdf_0) / epsilon
        central_difference = (cdf_plus - cdf_minus) / (2.0 * epsilon)
        linearisation_remainder = abs(cdf_plus - cdf_0 - epsilon * cdf_dot)
        wasserstein = math.sqrt(
            (mean_plus - mean_0) ** 2
            + (math.sqrt(variance_plus) - math.sqrt(variance_0)) ** 2
        )
        rows.append(
            {
                "epsilon": float(epsilon),
                "mean_plus": mean_plus,
                "variance_plus": variance_plus,
                "cdf_plus": cdf_plus,
                "analytic_cdf_derivative": cdf_dot,
                "forward_difference": forward_difference,
                "central_difference": central_difference,
                "forward_error": abs(forward_difference - cdf_dot),
                "central_error": abs(central_difference - cdf_dot),
                "cdf_linearisation_remainder": linearisation_remainder,
                "wasserstein_2": wasserstein,
            }
        )

    frame = pd.DataFrame(rows)

    A = np.asarray(model["A"])
    B = np.asarray(model["B"])
    G = np.asarray(model["G"])
    u0 = np.asarray(model["u0"])
    sigma = float(model["sigma"])
    epsilon_max = float(np.max(epsilons))
    stability_margin = min(
        -float(np.max(eigvalsh(A + epsilon * B)))
        for epsilon in np.linspace(-epsilon_max, epsilon_max, 101)
    )
    weights = np.asarray([weight(t, horizon) for t in t_grid])
    weight_l2_squared = float(np.trapezoid(np.sum(weights**2, axis=1), t_grid))
    deterministic_integral = float(
        np.trapezoid(t_grid**2 * np.exp(-2.0 * stability_margin * t_grid), t_grid)
    )
    stochastic_integral = float(
        np.trapezoid(
            (horizon - t_grid)
            * t_grid**2
            * np.exp(-2.0 * stability_margin * t_grid),
            t_grid,
        )
    )
    lipschitz_constant = float(
        norm(B, 2)
        * math.sqrt(weight_l2_squared)
        * math.sqrt(
            norm(u0) ** 2 * deterministic_integral
            + sigma**2 * norm(G, "fro") ** 2 * stochastic_integral
        )
    )
    frame["w2_common_noise_bound"] = lipschitz_constant * frame["epsilon"]

    frame.to_csv(out_dir / "wp6_operator_sensitivity_summary.csv", index=False)

    runtime = {
        "elapsed_seconds": time.perf_counter() - start,
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "dimension": int(model["dimension"]),
        "horizon": horizon,
        "sigma": sigma,
        "threshold": threshold,
        "baseline_mean": mean_0,
        "baseline_variance": variance_0,
        "analytic_mean_derivative": mean_dot,
        "analytic_variance_derivative": variance_dot,
        "analytic_cdf_derivative": cdf_dot,
        "operator_norm_B": float(norm(B, 2)),
        "stability_margin": stability_margin,
        "common_noise_lipschitz_constant": lipschitz_constant,
    }
    (out_dir / "wp6_runtime_diagnostics.json").write_text(
        json.dumps(runtime, indent=2), encoding="utf-8"
    )

    plt.figure(figsize=(7.6, 4.8))
    plt.loglog(frame["epsilon"], frame["forward_error"], marker="o", label="Forward difference")
    plt.loglog(frame["epsilon"], frame["central_error"], marker="s", label="Central difference")
    reference_1 = frame["forward_error"].iloc[-1] * (frame["epsilon"] / frame["epsilon"].iloc[-1])
    reference_2 = frame["central_error"].iloc[-1] * (frame["epsilon"] / frame["epsilon"].iloc[-1]) ** 2
    plt.loglog(frame["epsilon"], reference_1, linestyle="--", label="First-order slope")
    plt.loglog(frame["epsilon"], reference_2, linestyle=":", label="Second-order slope")
    plt.xlabel("Absolute perturbation size")
    plt.ylabel("Derivative approximation error")
    plt.title("WP6 analytic derivative versus finite differences")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "wp6_finite_difference_derivative.png", dpi=220)
    plt.close()

    plt.figure(figsize=(7.6, 4.8))
    plt.loglog(
        frame["epsilon"],
        frame["cdf_linearisation_remainder"],
        marker="o",
        label="Observed remainder",
    )
    reference = frame["cdf_linearisation_remainder"].iloc[-1] * (
        frame["epsilon"] / frame["epsilon"].iloc[-1]
    ) ** 2
    plt.loglog(frame["epsilon"], reference, linestyle="--", label="Second-order slope")
    plt.xlabel("Absolute perturbation size")
    plt.ylabel("Absolute CDF remainder")
    plt.title("WP6 first-order law linearisation")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "wp6_cdf_linearisation_remainder.png", dpi=220)
    plt.close()

    plt.figure(figsize=(7.6, 4.8))
    plt.plot(frame["epsilon"], frame["wasserstein_2"], marker="o", label="Exact Gaussian W2")
    plt.plot(
        frame["epsilon"],
        frame["w2_common_noise_bound"],
        linestyle="--",
        label="Common-noise Lipschitz bound",
    )
    plt.xlabel("Absolute perturbation size")
    plt.ylabel("Distance")
    plt.title("WP6 Wasserstein stability")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "wp6_wasserstein_stability.png", dpi=220)
    plt.close()

    print(frame.to_string(index=False, float_format=lambda value: f"{value:.8g}"))
    print(json.dumps(runtime, indent=2))


if __name__ == "__main__":
    main()
