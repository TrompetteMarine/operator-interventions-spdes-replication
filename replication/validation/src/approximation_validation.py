#!/usr/bin/env python3
"""WP7 validation: spatial, temporal, total-error, and bias-aware inference rates.

The calculations exploit exact Gaussian formulas for diagonal Ornstein-Uhlenbeck
modes. No Monte Carlo is needed for the spatial or temporal slopes. A final
simulation illustrates how numerical bias affects root-information inference.
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


def modal_constant_weight(lam, q, u0, c, a, horizon):
    x = a * lam * horizon
    mean = c * u0 * (-np.expm1(-x)) / (a * lam)
    bracket = (
        horizon
        - 2.0 * (-np.expm1(-x)) / (a * lam)
        + (-np.expm1(-2.0 * x)) / (2.0 * a * lam)
    )
    variance_primitive = q * q * c * c * bracket / (a * a * lam * lam)
    return mean, variance_primitive


def cdf_grid_distance(m0, v0, m1, v1, sigma, n_grid=6001):
    sd0 = sigma * math.sqrt(v0)
    sd1 = sigma * math.sqrt(v1)
    lo = min(m0 - 6.0 * sd0, m1 - 6.0 * sd1)
    hi = max(m0 + 6.0 * sd0, m1 + 6.0 * sd1)
    grid = np.linspace(lo, hi, n_grid)
    f0 = norm.cdf((grid - m0) / sd0)
    f1 = norm.cdf((grid - m1) / sd1)
    return float(np.max(np.abs(f0 - f1)))


def loglog_slope(x, y, tail=7):
    x = np.asarray(x, float)[-tail:]
    y = np.asarray(y, float)[-tail:]
    mask = (x > 0.0) & (y > 0.0)
    return float(np.polyfit(np.log(x[mask]), np.log(y[mask]), 1)[0])


def spatial_experiment(out_dir: Path):
    # Pointwise modal-decay corollary: d=1, r0=0.8, gamma=0.8, beta=0.
    # Constant-in-time modal weights gain an extra half spectral power over the generic L2-time bound.
    # Predicted K-slopes: mean = -(r0+gamma+1)=-2.6; variance = -4.6.
    a, sigma, horizon = 0.7, 0.8, 1.0
    r0, gamma, beta = 0.8, 0.8, 0.0
    k_max = 200_000
    k = np.arange(1, k_max + 1, dtype=float)
    lam = np.pi**2 * k**2
    q = lam ** (-beta / 2.0)
    u0 = lam ** (-r0 / 2.0)
    weight = lam ** (-gamma / 2.0)
    mean_modes, var_modes = modal_constant_weight(lam, q, u0, weight, a, horizon)
    cum_mean = np.cumsum(mean_modes)
    cum_var = np.cumsum(var_modes)
    mean_full = float(cum_mean[-1])
    var_full = float(cum_var[-1])

    levels = np.array([2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512])
    rows = []
    for K in levels:
        mean_k = float(cum_mean[K - 1])
        var_k = float(cum_var[K - 1])
        mean_tail = abs(mean_full - mean_k)
        var_tail = max(var_full - var_k, 0.0)
        w2 = math.sqrt(
            mean_tail**2
            + sigma**2 * (math.sqrt(var_full) - math.sqrt(var_k)) ** 2
        )
        cdf = cdf_grid_distance(mean_full, var_full, mean_k, var_k, sigma)
        strong_rms = math.sqrt(mean_tail**2 + sigma**2 * var_tail)
        rows.append(
            {
                "K": int(K),
                "mean_tail": mean_tail,
                "variance_tail": var_tail,
                "strong_functional_rms": strong_rms,
                "optimal_W2": w2,
                "cdf_sup": cdf,
            }
        )
    frame = pd.DataFrame(rows)
    frame.to_csv(out_dir / "wp7_spatial_rate_summary.csv", index=False)

    slopes = {
        "mean_tail": loglog_slope(frame["K"], frame["mean_tail"]),
        "variance_tail": loglog_slope(frame["K"], frame["variance_tail"]),
        "strong_functional_rms": loglog_slope(frame["K"], frame["strong_functional_rms"]),
        "optimal_W2": loglog_slope(frame["K"], frame["optimal_W2"]),
        "cdf_sup": loglog_slope(frame["K"], frame["cdf_sup"]),
        "predicted_mean": -(r0 + gamma + 1.0),
        "predicted_strong_rms": -min(r0 + gamma + 1.0, (2.0 * (beta + gamma + 2.0) - 1.0) / 2.0),
        "predicted_variance": -(2.0 * (beta + gamma + 2.0) - 1.0),
    }

    plt.figure(figsize=(7.6, 4.8))
    for col, label in [
        ("mean_tail", "Mean tail"),
        ("variance_tail", "Variance tail"),
        ("strong_functional_rms", "Strong functional RMS"),
        ("optimal_W2", "Optimal Gaussian W2"),
        ("cdf_sup", "Kolmogorov distance"),
    ]:
        plt.loglog(frame["K"], frame[col], marker="o", label=label)
    plt.xlabel("Galerkin level K")
    plt.ylabel("Approximation error")
    plt.title("WP7 spatial truncation rates")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(out_dir / "wp7_spatial_rates.png", dpi=210)
    plt.close()
    return frame, slopes, (mean_full, var_full)


def gauss_legendre_cell_integral(func, left, right, order=10):
    nodes, weights = np.polynomial.legendre.leggauss(order)
    points = 0.5 * (right - left) * nodes + 0.5 * (right + left)
    return 0.5 * (right - left) * float(np.sum(weights * func(points)))


def temporal_t_weight_params(J, K=8, a=0.7, horizon=1.0, r0=0.8, gamma=0.8, beta=0.0):
    """Exact and piecewise-left weight projection for w_k(t)=c_k t.

    The state is integrated exactly; only the deterministic weight is projected.
    """
    k = np.arange(1, K + 1, dtype=float)
    lam = np.pi**2 * k**2
    q = lam ** (-beta / 2.0)
    u0 = lam ** (-r0 / 2.0)
    ccoef = lam ** (-gamma / 2.0)
    dt = horizon / J

    mean_exact = 0.0
    var_exact = 0.0
    mean_disc = 0.0
    var_disc = 0.0

    for la, qq, uu, cc in zip(lam, q, u0, ccoef):
        rate = a * la
        x = rate * horizon
        mean_exact += cc * uu * (1.0 - (1.0 + x) * math.exp(-x)) / (rate * rate)

        def g_exact(s):
            ell = horizon - s
            return qq * cc * (
                s * (1.0 - np.exp(-rate * ell)) / rate
                + (1.0 - (1.0 + rate * ell) * np.exp(-rate * ell)) / (rate * rate)
            )

        var_exact += gauss_legendre_cell_integral(
            lambda s: g_exact(s) ** 2, 0.0, horizon, order=80
        )

        t_left = np.arange(J, dtype=float) * dt
        w_left = cc * t_left
        cell_exp = (np.exp(-rate * t_left) - np.exp(-rate * (t_left + dt))) / rate
        mean_disc += uu * float(np.sum(w_left * cell_exp))

        # A_l = sum_{j>l} w_j int_{t_j}^{t_{j+1}} exp(-rate(t-s))dt / exp(rate s)
        coeff = w_left * np.exp(-rate * t_left) * (1.0 - math.exp(-rate * dt)) / rate
        future = np.zeros(J)
        running = 0.0
        for ell in range(J - 1, -1, -1):
            future[ell] = running
            running += coeff[ell]

        for ell in range(J):
            left = ell * dt
            right = (ell + 1) * dt
            wl = w_left[ell]
            Af = future[ell]

            def g_disc(s):
                local = wl * (1.0 - np.exp(-rate * (right - s))) / rate
                return qq * (local + np.exp(rate * s) * Af)

            var_disc += gauss_legendre_cell_integral(
                lambda s: g_disc(s) ** 2, left, right, order=8
            )

    return mean_exact, var_exact, mean_disc, var_disc


def temporal_experiment(out_dir: Path):
    sigma = 0.8
    levels = np.array([8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512, 768, 1024])
    rows = []
    reference = temporal_t_weight_params(int(levels[-1]))[:2]
    mean_exact, var_exact = reference
    for J in levels:
        me, ve, md, vd = temporal_t_weight_params(int(J))
        assert abs(me - mean_exact) < 1e-11 and abs(ve - var_exact) < 1e-11
        w2 = math.sqrt(
            (md - me) ** 2 + sigma**2 * (math.sqrt(vd) - math.sqrt(ve)) ** 2
        )
        cdf = cdf_grid_distance(me, ve, md, vd, sigma)
        rows.append(
            {
                "J": int(J),
                "delta": 1.0 / J,
                "mean_error": abs(md - me),
                "variance_error": abs(vd - ve),
                "optimal_W2": w2,
                "cdf_sup": cdf,
            }
        )
    frame = pd.DataFrame(rows)
    frame.to_csv(out_dir / "wp7_temporal_rate_summary.csv", index=False)
    slopes = {
        col: loglog_slope(frame["delta"], frame[col])
        for col in ["mean_error", "variance_error", "optimal_W2", "cdf_sup"]
    }

    plt.figure(figsize=(7.4, 4.7))
    for col, label in [
        ("mean_error", "Mean error"),
        ("variance_error", "Variance error"),
        ("optimal_W2", "Optimal Gaussian W2"),
        ("cdf_sup", "Kolmogorov distance"),
    ]:
        plt.loglog(frame["delta"], frame[col], marker="o", label=label)
    plt.xlabel("Time step delta")
    plt.ylabel("Approximation error")
    plt.title("WP7 temporal weight-projection rates")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(out_dir / "wp7_temporal_rates.png", dpi=210)
    plt.close()
    return frame, slopes


def discrete_constant_weight_params(J, K, a, horizon=1.0, r0=0.8, gamma=0.8, beta=0.0):
    """Left rectangle functional using exact OU grid states, via exact Gaussian moments."""
    k = np.arange(1, K + 1, dtype=float)
    lam = np.pi**2 * k**2
    q = lam ** (-beta / 2.0)
    u0 = lam ** (-r0 / 2.0)
    ccoef = lam ** (-gamma / 2.0)
    dt = horizon / J
    rho = np.exp(-a * lam * dt)
    geom = (1.0 - rho**J) / (1.0 - rho)
    mean = float(np.sum(dt * ccoef * u0 * geom))

    # Stable closed forms for sum_{i,j=0}^{J-1} rho^{|i-j|}.
    sum_r = rho * (1.0 - rho ** (J - 1)) / (1.0 - rho)
    sum_hr = rho * (1.0 - J * rho ** (J - 1) + (J - 1) * rho**J) / (1.0 - rho) ** 2
    s_abs = J + 2.0 * (J * sum_r - sum_hr)
    s_sum = geom**2
    variance = float(
        np.sum(dt**2 * q * q * ccoef * ccoef / (2.0 * a * lam) * (s_abs - s_sum))
    )
    return mean, variance


def total_budget_experiment(out_dir: Path, full_params):
    mean_full, var_full = full_params
    a0, sigma, z = 0.7, 0.8, 0.02
    rho_space = 1.6
    exact_cdf = norm.cdf((z - mean_full) / (sigma * math.sqrt(var_full)))
    rates = np.array([20, 30, 40, 60, 80, 120, 160, 240, 320])
    rows = []
    for R in rates:
        Kb = max(2, int(math.ceil(R ** (1.0 / rho_space))))
        Jb = max(8, int(math.ceil(R)))
        eta_b = 1.0 / R
        mb, vb = discrete_constant_weight_params(Jb, Kb, a0 + eta_b)
        fb = norm.cdf((z - mb) / (sigma * math.sqrt(vb)))

        power = 1.7
        Ku = max(2, int(math.ceil(R ** (power / rho_space))))
        Ju = max(8, int(math.ceil(R**power)))
        eta_u = R ** (-power)
        mu, vu = discrete_constant_weight_params(Ju, Ku, a0 + eta_u)
        fu = norm.cdf((z - mu) / (sigma * math.sqrt(vu)))

        rows.extend(
            [
                {
                    "R": int(R),
                    "design": "balanced",
                    "K": Kb,
                    "J": Jb,
                    "operator_error": eta_b,
                    "cdf_bias": abs(fb - exact_cdf),
                    "normalised_bias": R * abs(fb - exact_cdf),
                },
                {
                    "R": int(R),
                    "design": "undersmoothed",
                    "K": Ku,
                    "J": Ju,
                    "operator_error": eta_u,
                    "cdf_bias": abs(fu - exact_cdf),
                    "normalised_bias": R * abs(fu - exact_cdf),
                },
            ]
        )
    frame = pd.DataFrame(rows)
    frame.to_csv(out_dir / "wp7_total_error_budget_summary.csv", index=False)

    plt.figure(figsize=(7.3, 4.6))
    for design in ["balanced", "undersmoothed"]:
        subset = frame[frame["design"] == design]
        plt.loglog(subset["R"], subset["cdf_bias"], marker="o", label=design)
    plt.loglog(rates, 1.0 / rates, linestyle="--", label="root-information scale R^-1")
    plt.xlabel("Information normalisation R")
    plt.ylabel("Uniform-law proxy bias")
    plt.title("WP7 total approximation budget")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "wp7_total_error_balance.png", dpi=210)
    plt.close()
    return frame, exact_cdf


def coverage_experiment(out_dir: Path, full_params, exact_cdf):
    mean_full, var_full = full_params
    a0, sigma, z = 0.7, 0.8, 0.02
    rho_space = 1.6
    rng = np.random.default_rng(20260707)
    reps = 100_000
    rows = []
    for R in [20, 40, 80, 160, 320]:
        for design in ["balanced", "undersmoothed"]:
            if design == "balanced":
                K = max(2, int(math.ceil(R ** (1.0 / rho_space))))
                J = max(8, int(math.ceil(R)))
                eta = 1.0 / R
            else:
                power = 1.7
                K = max(2, int(math.ceil(R ** (power / rho_space))))
                J = max(8, int(math.ceil(R**power)))
                eta = R ** (-power)
            m_num, v_num = discrete_constant_weight_params(J, K, a0 + eta)
            bias_bound = abs(norm.cdf((z - m_num) / (sigma * math.sqrt(v_num))) - exact_cdf)
            zdraw = rng.standard_normal(reps)
            sigma_hat = sigma + sigma / (math.sqrt(2.0) * R) * zdraw
            c = (z - m_num) / (sigma_hat * math.sqrt(v_num))
            estimate = norm.cdf(c)
            derivative = np.abs(-c * norm.pdf(c) / sigma_hat)
            half = norm.ppf(0.975) * derivative * sigma_hat / (math.sqrt(2.0) * R)
            naive = np.mean((exact_cdf >= estimate - half) & (exact_cdf <= estimate + half))
            enlarged = np.mean(
                (exact_cdf >= estimate - half - bias_bound)
                & (exact_cdf <= estimate + half + bias_bound)
            )
            rows.append(
                {
                    "R": int(R),
                    "design": design,
                    "K": K,
                    "J": J,
                    "normalised_bias": R * bias_bound,
                    "naive_coverage": float(naive),
                    "bias_enlarged_coverage": float(enlarged),
                    "reps": reps,
                }
            )
    frame = pd.DataFrame(rows)
    frame.to_csv(out_dir / "wp7_inference_coverage_summary.csv", index=False)

    plt.figure(figsize=(7.4, 4.7))
    for design, marker in [("balanced", "o"), ("undersmoothed", "s")]:
        subset = frame[frame["design"] == design]
        plt.plot(subset["R"], subset["naive_coverage"], marker=marker, label=f"{design}: naive")
        plt.plot(
            subset["R"],
            subset["bias_enlarged_coverage"],
            marker=marker,
            linestyle="--",
            label=f"{design}: bias enlarged",
        )
    plt.axhline(0.95, linestyle=":", label="Nominal 95%")
    plt.xscale("log")
    plt.ylim(-0.02, 1.01)
    plt.xlabel("Information normalisation R")
    plt.ylabel("Coverage")
    plt.title("WP7 numerical bias and simultaneous-inference logic")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(out_dir / "wp7_bias_coverage.png", dpi=210)
    plt.close()
    return frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    spatial, spatial_slopes, full_params = spatial_experiment(out_dir)
    temporal, temporal_slopes = temporal_experiment(out_dir)
    total, exact_cdf = total_budget_experiment(out_dir, full_params)
    coverage = coverage_experiment(out_dir, full_params, exact_cdf)
    elapsed = time.perf_counter() - start

    summary = {
        "spatial_slopes": spatial_slopes,
        "temporal_slopes": temporal_slopes,
        "elapsed_seconds": elapsed,
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
    }
    (out_dir / "wp7_runtime_diagnostics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("\nSpatial tail:\n", spatial.tail().to_string(index=False))
    print("\nTemporal tail:\n", temporal.tail().to_string(index=False))
    print("\nTotal budget:\n", total.to_string(index=False))
    print("\nCoverage:\n", coverage.to_string(index=False))


if __name__ == "__main__":
    main()
