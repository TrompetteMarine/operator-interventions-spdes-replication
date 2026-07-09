#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.stats import kstest, norm, probplot, skew, kurtosis


def heat_spectrum(N: int) -> np.ndarray:
    k = np.arange(1, N + 1, dtype=float)
    return np.pi**2 * k**2


def noise_coefficients(N: int, alpha_q: float) -> np.ndarray:
    k = np.arange(1, N + 1, dtype=float)
    return k ** (-alpha_q)


def simulate_sufficient_statistics(
    N: int,
    n: int,
    reps: int,
    theta0: float,
    sigma0: float,
    horizon: float,
    alpha_q: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    rng = np.random.default_rng(seed)
    lam = heat_spectrum(N)
    q = noise_coefficients(N, alpha_q)
    dt = horizon / n
    rho = np.exp(-theta0 * lam * dt)
    h = -np.expm1(-2.0 * theta0 * lam * dt) / (2.0 * theta0 * lam)
    innovation_sd = sigma0 * q * np.sqrt(h)
    y = np.zeros((reps, N), dtype=float)
    sxx = np.zeros_like(y)
    sxy = np.zeros_like(y)
    syy = np.zeros_like(y)
    for _ in range(n):
        y_next = rho * y + innovation_sd * rng.standard_normal((reps, N))
        sxx += y * y
        sxy += y * y_next
        syy += y_next * y_next
        y = y_next
    return sxx, sxy, syy, lam, q, dt


def exact_profile_mle(
    sxx: np.ndarray,
    sxy: np.ndarray,
    syy: np.ndarray,
    lam: np.ndarray,
    q: np.ndarray,
    dt: float,
    n: int,
    theta_bounds: tuple[float, float],
) -> tuple[np.ndarray, np.ndarray]:
    reps, N = sxx.shape
    theta_hat = np.empty(reps)
    sigma_hat = np.empty(reps)

    def objective(theta: float, r: int) -> float:
        rho = np.exp(-theta * lam * dt)
        h = -np.expm1(-2.0 * theta * lam * dt) / (2.0 * theta * lam)
        rss = np.sum((syy[r] - 2.0 * rho * sxy[r] + rho * rho * sxx[r]) / (q * q * h))
        sigma2 = max(rss / (N * n), np.finfo(float).tiny)
        return N * n * math.log(sigma2) + n * float(np.sum(np.log(q * q * h)))

    for r in range(reps):
        result = minimize_scalar(
            objective,
            args=(r,),
            method="bounded",
            bounds=theta_bounds,
            options={"xatol": 1e-9, "maxiter": 160},
        )
        if not result.success:
            raise RuntimeError(result.message)
        theta_hat[r] = result.x
        rho = np.exp(-result.x * lam * dt)
        h = -np.expm1(-2.0 * result.x * lam * dt) / (2.0 * result.x * lam)
        rss = np.sum((syy[r] - 2.0 * rho * sxy[r] + rho * rho * sxx[r]) / (q * q * h))
        sigma_hat[r] = math.sqrt(max(rss / (N * n), 0.0))
    return theta_hat, sigma_hat


def loglikelihood(
    theta: float,
    sigma: float,
    sxx: np.ndarray,
    sxy: np.ndarray,
    syy: np.ndarray,
    lam: np.ndarray,
    q: np.ndarray,
    dt: float,
    n: int,
) -> np.ndarray:
    rho = np.exp(-theta * lam * dt)
    h = -np.expm1(-2.0 * theta * lam * dt) / (2.0 * theta * lam)
    v = sigma * sigma * q * q * h
    rss = syy - 2.0 * rho * sxy + rho * rho * sxx
    return -0.5 * (n * np.sum(np.log(2.0 * np.pi * v)) + np.sum(rss / v, axis=1))


def score_blocks(
    theta: float,
    sigma: float,
    sxx: np.ndarray,
    sxy: np.ndarray,
    syy: np.ndarray,
    lam: np.ndarray,
    q: np.ndarray,
    dt: float,
    n: int,
) -> np.ndarray:
    rho = np.exp(-theta * lam * dt)
    h = -np.expm1(-2.0 * theta * lam * dt) / (2.0 * theta * lam)
    v = sigma * sigma * q * q * h
    dot_rho = -lam * dt * rho
    g = 2.0 * lam * dt / np.expm1(2.0 * theta * lam * dt) - 1.0 / theta
    rss = syy - 2.0 * rho * sxy + rho * rho * sxx
    ry = sxy - rho * sxx
    score_theta = dot_rho * ry / v + 0.5 * (rss / v - n) * g
    score_sigma = (rss / v - n) / sigma
    return np.stack([score_theta, score_sigma], axis=-1)


def target_variance_primitive(
    a: float | np.ndarray,
    K: int,
    alpha_q: float,
    weight_exponent: float,
    horizon: float,
) -> np.ndarray:
    a_arr = np.atleast_1d(np.asarray(a, dtype=float))
    k = np.arange(1, K + 1, dtype=float)
    lam = np.pi**2 * k**2
    q = k ** (-alpha_q)
    c = k ** (-weight_exponent)
    out = []
    for av in a_arr:
        rate = av * lam
        bracket = (
            horizon
            - 2.0 * (-np.expm1(-rate * horizon)) / rate
            + (-np.expm1(-2.0 * rate * horizon)) / (2.0 * rate)
        )
        out.append(float(np.sum(q * q * c * c * bracket / (rate * rate))))
    return np.asarray(out)


def target_surfaces(
    theta: float,
    sigma: float,
    theta0: float,
    sigma0: float,
    theta_intervention: float,
    a_grid: np.ndarray,
    m_grid: np.ndarray,
    K: int,
    alpha_q: float,
    weight_exponent: float,
    horizon: float,
) -> dict[str, np.ndarray]:
    v_cf = target_variance_primitive(a_grid, K, alpha_q, weight_exponent, horizon)
    v_cf_true = v_cf
    z_blocks = [m_grid * sigma0 * math.sqrt(v) for v in v_cf_true]
    z = np.concatenate(z_blocks)
    v_repeat = np.repeat(v_cf, len(m_grid))
    c_cf = z / (sigma * np.sqrt(v_repeat))
    cdf_cf = norm.cdf(c_cf)
    v_fact = float(target_variance_primitive(theta, K, alpha_q, weight_exponent, horizon)[0])
    cdf_fact = norm.cdf(z / (sigma * math.sqrt(v_fact)))
    return {"z": z, "v_cf": v_repeat, "cdf_cf": cdf_cf, "cdf_fact": cdf_fact, "effect": cdf_cf - cdf_fact}


def dtheta_factual_surface(
    theta: float,
    sigma: float,
    z: np.ndarray,
    K: int,
    alpha_q: float,
    weight_exponent: float,
    horizon: float,
) -> np.ndarray:
    step = max(1e-6, 2e-5 * theta)
    vp = float(target_variance_primitive(theta + step, K, alpha_q, weight_exponent, horizon)[0])
    vm = float(target_variance_primitive(theta - step, K, alpha_q, weight_exponent, horizon)[0])
    fp = norm.cdf(z / (sigma * math.sqrt(vp)))
    fm = norm.cdf(z / (sigma * math.sqrt(vm)))
    return (fp - fm) / (2.0 * step)


def design_audit(config: dict[str, Any], tables: Path) -> pd.DataFrame:
    rows = []
    T = float(config["canonical"]["horizon"])
    for N in config["planned_grid_audit"]["N"]:
        for n in config["planned_grid_audit"]["n"]:
            value = float(np.pi**2 * N * N * T / n)
            status = "resolved" if value <= 0.15 else ("transitional" if value <= 0.5 else "unresolved")
            rows.append({"N": N, "n": n, "lambda_N_Delta": value, "regime_status": status})
    frame = pd.DataFrame(rows)
    frame.to_csv(tables / "planned_grid_regime_audit.csv", index=False)
    return frame


def summarise_design(
    label: str,
    N: int,
    n: int,
    alpha_q: float,
    theta_hat: np.ndarray,
    sigma_hat: np.ndarray,
    theta0: float,
    sigma0: float,
    horizon: float,
    lam: np.ndarray,
) -> dict[str, float | int | str]:
    Lambda = float(np.sum(lam))
    se_theta = np.sqrt(2.0 * theta_hat / horizon / Lambda)
    se_sigma = sigma_hat / math.sqrt(2.0 * N * n)
    zt = np.sqrt(Lambda) * (theta_hat - theta0) / math.sqrt(2.0 * theta0 / horizon)
    zs = math.sqrt(N * n) * (sigma_hat - sigma0) / (sigma0 / math.sqrt(2.0))
    return {
        "design": label,
        "N": N,
        "n": n,
        "alpha_q": alpha_q,
        "Delta": horizon / n,
        "lambda_N_Delta": float(lam[-1] * horizon / n),
        "Lambda_N": Lambda,
        "reps": len(theta_hat),
        "theta_bias": float(np.mean(theta_hat - theta0)),
        "theta_rmse": float(np.sqrt(np.mean((theta_hat - theta0) ** 2))),
        "theta_empirical_sd": float(np.std(theta_hat, ddof=1)),
        "theta_average_se": float(np.mean(se_theta)),
        "sigma_bias": float(np.mean(sigma_hat - sigma0)),
        "sigma_rmse": float(np.sqrt(np.mean((sigma_hat - sigma0) ** 2))),
        "sigma_empirical_sd": float(np.std(sigma_hat, ddof=1)),
        "sigma_average_se": float(np.mean(se_sigma)),
        "ztheta_mean": float(np.mean(zt)),
        "ztheta_sd": float(np.std(zt, ddof=1)),
        "ztheta_skew": float(skew(zt, bias=False)),
        "ztheta_excess_kurtosis": float(kurtosis(zt, fisher=True, bias=False)),
        "ztheta_ks_pvalue": float(kstest(zt, "norm").pvalue),
        "zsigma_mean": float(np.mean(zs)),
        "zsigma_sd": float(np.std(zs, ddof=1)),
        "zsigma_skew": float(skew(zs, bias=False)),
        "zsigma_excess_kurtosis": float(kurtosis(zs, fisher=True, bias=False)),
        "zsigma_ks_pvalue": float(kstest(zs, "norm").pvalue),
        "scaled_cross_correlation": float(np.corrcoef(zt, zs)[0, 1]),
    }


def counterfactual_diagnostics(
    design: str,
    N: int,
    n: int,
    alpha_q: float,
    theta_hat: np.ndarray,
    sigma_hat: np.ndarray,
    config: dict[str, Any],
) -> tuple[dict[str, float | int | str], pd.DataFrame, pd.DataFrame]:
    can = config["canonical"]
    cf = config["counterfactual"]
    theta0 = float(can["theta0"])
    sigma0 = float(can["sigma0"])
    horizon = float(can["horizon"])
    K = int(cf["target_modes"])
    s = float(can["weight_exponent"])
    a_grid = np.asarray(cf["intervention_grid"], dtype=float)
    m_grid = np.asarray(cf["standardised_thresholds"], dtype=float)
    p_grid = np.asarray(cf["quantile_levels"], dtype=float)
    truth = target_surfaces(theta0, sigma0, theta0, sigma0, float(can["theta_intervention"]), a_grid, m_grid, K, alpha_q, s, horizon)
    z = truth["z"]
    cdf_true = truth["cdf_cf"]
    effect_true = truth["effect"]
    v_cf = target_variance_primitive(a_grid, K, alpha_q, s, horizon)
    v_fact_true = float(target_variance_primitive(theta0, K, alpha_q, s, horizon)[0])
    Lambda = float(np.sum(heat_spectrum(N)))
    a_rate = math.sqrt(Lambda)
    b_rate = math.sqrt(N * n)

    sup_cdf = np.empty(len(theta_hat))
    sup_effect = np.empty(len(theta_hat))
    pointwise_abs = np.empty(len(theta_hat))
    tail_abs = np.empty(len(theta_hat))
    fast_cover = np.empty(len(theta_hat), dtype=bool)
    slow_cover = np.empty(len(theta_hat), dtype=bool)
    fast_width = np.empty(len(theta_hat))
    slow_width = np.empty(len(theta_hat))
    quantile_errors = {float(p): np.empty(len(theta_hat)) for p in p_grid}
    point_cover = np.zeros((len(theta_hat), len(z)), dtype=bool)

    idx_point = int(np.where(np.isclose(m_grid, 1.0))[0][0])
    idx_point = idx_point  # first intervention block

    for r, (th, sg) in enumerate(zip(theta_hat, sigma_hat)):
        est = target_surfaces(th, sg, theta0, sigma0, float(can["theta_intervention"]), a_grid, m_grid, K, alpha_q, s, horizon)
        cdf_hat = est["cdf_cf"]
        effect_hat = est["effect"]
        sup_cdf[r] = np.max(np.abs(cdf_hat - cdf_true))
        sup_effect[r] = np.max(np.abs(effect_hat - effect_true))
        pointwise_abs[r] = abs(cdf_hat[idx_point] - cdf_true[idx_point])
        tail_abs[r] = abs((1.0 - cdf_hat[idx_point]) - (1.0 - cdf_true[idx_point]))

        c_hat = z / (sg * np.sqrt(truth["v_cf"]))
        d_sigma = -c_hat * norm.pdf(c_hat) / sg
        se_point = np.abs(d_sigma) * sg / math.sqrt(2.0) / b_rate
        half_point = norm.ppf(0.975) * se_point
        point_cover[r] = (cdf_true >= cdf_hat - half_point) & (cdf_true <= cdf_hat + half_point)
        fast_half = norm.ppf(0.975) * np.max(np.abs(d_sigma)) * sg / math.sqrt(2.0) / b_rate
        fast_cover[r] = np.all(np.abs(cdf_hat - cdf_true) <= fast_half)
        fast_width[r] = 2.0 * fast_half

        dtheta = dtheta_factual_surface(th, sg, z, K, alpha_q, s, horizon)
        slow_half = norm.ppf(0.975) * np.max(np.abs(dtheta)) * math.sqrt(2.0 * th / horizon) / a_rate
        slow_cover[r] = np.all(np.abs(effect_hat - effect_true) <= slow_half)
        slow_width[r] = 2.0 * slow_half

        for p in p_grid:
            q_true = sigma0 * np.sqrt(v_cf) * norm.ppf(p)
            q_hat = sg * np.sqrt(v_cf) * norm.ppf(p)
            quantile_errors[float(p)][r] = float(np.max(np.abs(q_hat - q_true)))

    region = np.tile(np.where(np.abs(m_grid) <= 0.5, "centre", np.where(np.abs(m_grid) <= 1.0, "shoulder", "tail")), len(a_grid))
    pc_rows = []
    for j in range(len(z)):
        pc_rows.append({
            "design": design,
            "N": N,
            "n": n,
            "alpha_q": alpha_q,
            "a": float(np.repeat(a_grid, len(m_grid))[j]),
            "standardised_threshold": float(np.tile(m_grid, len(a_grid))[j]),
            "region": str(region[j]),
            "coverage": float(np.mean(point_cover[:, j])),
        })
    point_frame = pd.DataFrame(pc_rows)
    region_frame = point_frame.groupby(["design", "N", "n", "alpha_q", "region"], as_index=False)["coverage"].agg(["mean", "min", "max"]).reset_index()

    row: dict[str, float | int | str] = {
        "design": design,
        "N": N,
        "n": n,
        "alpha_q": alpha_q,
        "reps": len(theta_hat),
        "cdf_sup_mean": float(np.mean(sup_cdf)),
        "cdf_sup_rmse": float(np.sqrt(np.mean(sup_cdf**2))),
        "cdf_point_mean_abs": float(np.mean(pointwise_abs)),
        "tail_probability_mean_abs": float(np.mean(tail_abs)),
        "effect_sup_mean": float(np.mean(sup_effect)),
        "effect_sup_rmse": float(np.sqrt(np.mean(sup_effect**2))),
        "fast_simultaneous_coverage": float(np.mean(fast_cover)),
        "slow_simultaneous_coverage": float(np.mean(slow_cover)),
        "fast_average_full_width": float(np.mean(fast_width)),
        "slow_average_full_width": float(np.mean(slow_width)),
        "pointwise_coverage_min": float(point_frame["coverage"].min()),
        "pointwise_coverage_max": float(point_frame["coverage"].max()),
    }
    for p, errors in quantile_errors.items():
        row[f"quantile_{p:.2f}_mean_abs"] = float(np.mean(errors))
        row[f"quantile_{p:.2f}_rmse"] = float(np.sqrt(np.mean(errors**2)))
    return row, point_frame, region_frame


def likelihood_ratio_diagnostic(
    N: int,
    n: int,
    sxx: np.ndarray,
    sxy: np.ndarray,
    syy: np.ndarray,
    lam: np.ndarray,
    q: np.ndarray,
    dt: float,
    theta0: float,
    sigma0: float,
    horizon: float,
) -> dict[str, float]:
    Lambda = float(np.sum(lam))
    a_rate, b_rate = math.sqrt(Lambda), math.sqrt(N * n)
    hvec = np.asarray([0.30, -0.20])
    theta_local = theta0 + hvec[0] / a_rate
    sigma_local = sigma0 + hvec[1] / b_rate
    exact = loglikelihood(theta_local, sigma_local, sxx, sxy, syy, lam, q, dt, n) - loglikelihood(theta0, sigma0, sxx, sxy, syy, lam, q, dt, n)
    blocks = score_blocks(theta0, sigma0, sxx, sxy, syy, lam, q, dt, n)
    score = np.sum(blocks, axis=1)
    delta = score * np.asarray([1.0 / a_rate, 1.0 / b_rate])
    J = np.diag([horizon / (2.0 * theta0), 2.0 / sigma0**2])
    approx = delta @ hvec - 0.5 * float(hvec @ J @ hvec)
    rem = exact - approx
    return {
        "lr_exact_mean": float(np.mean(exact)),
        "lr_approx_mean": float(np.mean(approx)),
        "lr_remainder_mean": float(np.mean(rem)),
        "lr_remainder_rmse": float(np.sqrt(np.mean(rem**2))),
        "lr_exact_approx_correlation": float(np.corrcoef(exact, approx)[0, 1]),
    }


def bootstrap_sensitivity(
    cached: dict[str, Any],
    config: dict[str, Any],
    tables: Path,
) -> pd.DataFrame:
    bs = config["bootstrap_sensitivity"]
    can = config["canonical"]
    cf = config["counterfactual"]
    reps = min(int(bs["reps"]), cached["sxx"].shape[0])
    N, n = cached["N"], cached["n"]
    lam, q, dt = cached["lam"], cached["q"], cached["dt"]
    sxx, sxy, syy = cached["sxx"][:reps], cached["sxy"][:reps], cached["syy"][:reps]
    thhat, sighat = cached["theta_hat"][:reps], cached["sigma_hat"][:reps]
    theta0, sigma0, horizon = float(can["theta0"]), float(can["sigma0"]), float(can["horizon"])
    alpha_q, K, s = float(can["alpha_q"]), int(cf["target_modes"]), float(can["weight_exponent"])
    a_grid = np.asarray(cf["intervention_grid"], dtype=float)
    Lambda = float(np.sum(lam))
    a_rate, b_rate = math.sqrt(Lambda), math.sqrt(N * n)
    rng = np.random.default_rng(int(config["seed"]) + 88888)
    rows = []

    # One-factor-at-a-time sensitivity avoids an unnecessary full Cartesian product.
    base_draws = 499
    base_grid = 31
    experiments = []
    experiments.extend((method, base_draws, base_grid, "multiplier") for method in bs["methods"])
    experiments.extend(("direct_gaussian", int(draws), base_grid, "draw_count") for draws in bs["draw_counts"] if int(draws) != base_draws)
    experiments.extend(("direct_gaussian", base_draws, int(grid), "grid_resolution") for grid in bs["grid_sizes"] if int(grid) != base_grid)
    for method, draws, grid_size, sensitivity_axis in experiments:
        m_grid = np.linspace(-2.5, 2.5, int(grid_size))
        truth = target_surfaces(theta0, sigma0, theta0, sigma0, float(can["theta_intervention"]), a_grid, m_grid, K, alpha_q, s, horizon)
        z, cdf_true, effect_true = truth["z"], truth["cdf_cf"], truth["effect"]
        fast_cov = []
        slow_cov = []
        fast_width = []
        slow_width = []
        for r in range(reps):
            th, sg = float(thhat[r]), float(sighat[r])
            est = target_surfaces(th, sg, theta0, sigma0, float(can["theta_intervention"]), a_grid, m_grid, K, alpha_q, s, horizon)
            c_hat = z / (sg * np.sqrt(truth["v_cf"]))
            ds = -c_hat * norm.pdf(c_hat) / sg
            dth = dtheta_factual_surface(th, sg, z, K, alpha_q, s, horizon)
            if method == "direct_gaussian":
                htheta = math.sqrt(2.0 * th / horizon) * rng.standard_normal(draws)
                hsigma = sg / math.sqrt(2.0) * rng.standard_normal(draws)
            else:
                blocks = score_blocks(th, sg, sxx[r:r+1], sxy[r:r+1], syy[r:r+1], lam, q, dt, n)[0]
                scaled = blocks * np.asarray([1.0 / a_rate, 1.0 / b_rate])
                Jhat = scaled.T @ scaled
                eig, vec = np.linalg.eigh(Jhat)
                eig = np.maximum(eig, max(1e-10, 1e-8 * float(np.max(eig))))
                Jinv = vec @ np.diag(1.0 / eig) @ vec.T
                if method == "mode_gaussian":
                    xi = rng.standard_normal((draws, N))
                else:
                    xi = rng.choice(np.asarray([-1.0, 1.0]), size=(draws, N))
                hstar = (xi @ scaled) @ Jinv.T
                htheta, hsigma = hstar[:, 0], hstar[:, 1]
            crit_fast = float(np.quantile(np.max(np.abs(ds))[None] * np.abs(hsigma), 0.95))
            crit_slow = float(np.quantile(np.max(np.abs(dth))[None] * np.abs(htheta), 0.95))
            fast_cov.append(float(np.all(np.abs(est["cdf_cf"] - cdf_true) <= crit_fast / b_rate)))
            slow_cov.append(float(np.all(np.abs(est["effect"] - effect_true) <= crit_slow / a_rate)))
            fast_width.append(2.0 * crit_fast / b_rate)
            slow_width.append(2.0 * crit_slow / a_rate)
        rows.append({
            "sensitivity_axis": sensitivity_axis,
            "method": method,
            "draws": int(draws),
            "grid_size": int(grid_size),
            "reps": reps,
            "N": N,
            "n": n,
            "fast_coverage": float(np.mean(fast_cov)),
            "slow_coverage": float(np.mean(slow_cov)),
            "fast_mean_full_width": float(np.mean(fast_width)),
            "slow_mean_full_width": float(np.mean(slow_width)),
        })
    frame = pd.DataFrame(rows)
    frame.to_csv(tables / "bootstrap_sensitivity.csv", index=False)
    return frame


def make_figures(
    estimation: pd.DataFrame,
    raw: pd.DataFrame,
    lr: pd.DataFrame,
    counter: pd.DataFrame,
    pointwise: pd.DataFrame,
    bootstrap: pd.DataFrame,
    figures: Path,
) -> None:
    core = raw[raw["experiment"] == "core"].copy()
    max_N = int(core["N"].max())
    largest = core[core["N"] == max_N]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.2))
    axes[0].hist(largest["ztheta_standard"], bins=30, density=True)
    x = np.linspace(-3.5, 3.5, 400)
    axes[0].plot(x, norm.pdf(x))
    axes[0].set_title(r"$Z_\theta$ at largest design")
    axes[1].hist(largest["zsigma_standard"], bins=30, density=True)
    axes[1].plot(x, norm.pdf(x))
    axes[1].set_title(r"$Z_\sigma$ at largest design")
    fig.tight_layout()
    fig.savefig(figures / "lan_histograms.png", dpi=210)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.2))
    for ax, col, title in [(axes[0], "ztheta_standard", r"$Z_\theta$"), (axes[1], "zsigma_standard", r"$Z_\sigma$")]:
        osm, osr = probplot(largest[col], dist="norm", fit=False)
        ax.scatter(osm, osr, s=10)
        lo = min(float(np.min(osm)), float(np.min(osr)))
        hi = max(float(np.max(osm)), float(np.max(osr)))
        ax.plot([lo, hi], [lo, hi], linestyle="--")
        ax.set_title(title)
        ax.set_xlabel("Theoretical quantile")
        ax.set_ylabel("Empirical quantile")
    fig.tight_layout()
    fig.savefig(figures / "lan_qq_plots.png", dpi=210)
    plt.close(fig)

    plt.figure(figsize=(7.2, 4.5))
    plt.plot(estimation["N"], estimation["ztheta_sd"], marker="o", label=r"SD($Z_\theta$)")
    plt.plot(estimation["N"], estimation["zsigma_sd"], marker="s", label=r"SD($Z_\sigma$)")
    plt.axhline(1.0, linestyle="--", label="Standard normal")
    plt.xlabel("Observed modes N")
    plt.ylabel("Information-standardised SD")
    plt.title("LAN covariance convergence")
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures / "lan_covariance_convergence.png", dpi=210)
    plt.close()

    plt.figure(figsize=(7.2, 4.5))
    plt.plot(lr["N"], lr["lr_remainder_rmse"], marker="o")
    plt.yscale("log")
    plt.xlabel("Observed modes N")
    plt.ylabel("RMSE of LAN likelihood-ratio remainder")
    plt.title("Likelihood-ratio quadratic approximation")
    plt.tight_layout()
    plt.savefig(figures / "lan_likelihood_ratio_remainder.png", dpi=210)
    plt.close()

    plt.figure(figsize=(7.4, 4.6))
    plt.plot(counter["N"], counter["cdf_sup_rmse"], marker="o", label="Counterfactual CDF sup RMSE")
    plt.plot(counter["N"], counter["effect_sup_rmse"], marker="s", label="Distributional-effect sup RMSE")
    plt.yscale("log")
    plt.xlabel("Observed modes N")
    plt.ylabel("Error")
    plt.title("Counterfactual target error")
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures / "counterfactual_target_errors.png", dpi=210)
    plt.close()

    piv = pointwise.pivot_table(index="standardised_threshold", columns="N", values="coverage", aggfunc="mean")
    plt.figure(figsize=(7.4, 4.6))
    for col in piv.columns:
        plt.plot(piv.index, piv[col], marker="o", label=f"N={col}")
    plt.axhline(0.95, linestyle="--", label="Nominal")
    plt.ylim(0.85, 1.0)
    plt.xlabel("Standardised threshold")
    plt.ylabel("Pointwise coverage")
    plt.title("Coverage by target region")
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures / "pointwise_coverage_by_threshold.png", dpi=210)
    plt.close()

    subset = bootstrap[bootstrap["sensitivity_axis"] == "multiplier"].copy()
    x = np.arange(len(subset))
    plt.figure(figsize=(8.0, 4.6))
    plt.plot(x, subset["fast_coverage"], marker="o", label="Fast CDF")
    plt.plot(x, subset["slow_coverage"], marker="s", label="Slow effect")
    plt.axhline(0.95, linestyle="--", label="Nominal")
    plt.xticks(x, subset["method"], rotation=15)
    plt.ylim(0.85, 1.0)
    plt.ylabel("Simultaneous coverage")
    plt.title("Multiplier-distribution sensitivity")
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures / "bootstrap_multiplier_sensitivity.png", dpi=210)
    plt.close()


def run(config: dict[str, Any], root: Path) -> dict[str, Any]:
    tables = root / "results" / "tables"
    raw_dir = root / "results" / "raw"
    figures = root / "results" / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    audit = design_audit(config, tables)
    can = config["canonical"]
    theta0, sigma0, horizon = float(can["theta0"]), float(can["sigma0"]), float(can["horizon"])
    alpha_default = float(can["alpha_q"])
    seed0 = int(config["seed"])

    estimation_rows = []
    lr_rows = []
    counter_rows = []
    pointwise_frames = []
    region_frames = []
    raw_frames = []
    cache = None

    for idx, design in enumerate(config["theorem_aligned_designs"]):
        N, n, reps = int(design["N"]), int(design["n"]), int(design["reps"])
        label = f"N{N}_n{n}_alpha{alpha_default:g}"
        sxx, sxy, syy, lam, q, dt = simulate_sufficient_statistics(N, n, reps, theta0, sigma0, horizon, alpha_default, seed0 + idx * 1000)
        theta_hat, sigma_hat = exact_profile_mle(sxx, sxy, syy, lam, q, dt, n, (0.03, 0.40))
        estimation_rows.append(summarise_design(label, N, n, alpha_default, theta_hat, sigma_hat, theta0, sigma0, horizon, lam))
        lr = likelihood_ratio_diagnostic(N, n, sxx, sxy, syy, lam, q, dt, theta0, sigma0, horizon)
        lr_rows.append({"design": label, "N": N, "n": n, **lr})
        counter, point, region = counterfactual_diagnostics(label, N, n, alpha_default, theta_hat, sigma_hat, config)
        counter_rows.append(counter)
        pointwise_frames.append(point)
        region_frames.append(region)
        Lambda = float(np.sum(lam))
        raw_frames.append(pd.DataFrame({
            "experiment": "core",
            "design": label,
            "N": N,
            "n": n,
            "alpha_q": alpha_default,
            "replicate": np.arange(reps),
            "theta_hat": theta_hat,
            "sigma_hat": sigma_hat,
            "ztheta_standard": np.sqrt(Lambda) * (theta_hat - theta0) / math.sqrt(2.0 * theta0 / horizon),
            "zsigma_standard": math.sqrt(N * n) * (sigma_hat - sigma0) / (sigma0 / math.sqrt(2.0)),
        }))
        if N == int(config["bootstrap_sensitivity"]["source_design_N"]):
            cache = {"N": N, "n": n, "sxx": sxx, "sxy": sxy, "syy": syy, "lam": lam, "q": q, "dt": dt, "theta_hat": theta_hat, "sigma_hat": sigma_hat}

    # Noise-smoothness sensitivity; reuse core alpha if available.
    sens = config["alpha_sensitivity"]
    for j, alpha_q in enumerate(sens["values"]):
        alpha_q = float(alpha_q)
        if math.isclose(alpha_q, alpha_default):
            continue
        N, n, reps = int(sens["N"]), int(sens["n"]), int(sens["reps"])
        label = f"alpha_sensitivity_{alpha_q:g}"
        sxx, sxy, syy, lam, q, dt = simulate_sufficient_statistics(N, n, reps, theta0, sigma0, horizon, alpha_q, seed0 + 9000 + j * 1000)
        theta_hat, sigma_hat = exact_profile_mle(sxx, sxy, syy, lam, q, dt, n, (0.03, 0.40))
        estimation_rows.append(summarise_design(label, N, n, alpha_q, theta_hat, sigma_hat, theta0, sigma0, horizon, lam))
        Lambda = float(np.sum(lam))
        raw_frames.append(pd.DataFrame({
            "experiment": "alpha_sensitivity",
            "design": label,
            "N": N,
            "n": n,
            "alpha_q": alpha_q,
            "replicate": np.arange(reps),
            "theta_hat": theta_hat,
            "sigma_hat": sigma_hat,
            "ztheta_standard": np.sqrt(Lambda) * (theta_hat - theta0) / math.sqrt(2.0 * theta0 / horizon),
            "zsigma_standard": math.sqrt(N * n) * (sigma_hat - sigma0) / (sigma0 / math.sqrt(2.0)),
        }))

    if cache is None:
        raise RuntimeError("Bootstrap source design was not simulated")
    bootstrap = bootstrap_sensitivity(cache, config, tables)
    estimation = pd.DataFrame(estimation_rows)
    lr_frame = pd.DataFrame(lr_rows)
    counter_frame = pd.DataFrame(counter_rows)
    pointwise = pd.concat(pointwise_frames, ignore_index=True)
    regions = pd.concat(region_frames, ignore_index=True)
    raw = pd.concat(raw_frames, ignore_index=True)

    estimation.to_csv(tables / "estimation_summary.csv", index=False)
    lr_frame.to_csv(tables / "lan_likelihood_ratio_summary.csv", index=False)
    counter_frame.to_csv(tables / "counterfactual_summary.csv", index=False)
    pointwise.to_csv(tables / "pointwise_coverage.csv", index=False)
    regions.to_csv(tables / "regional_coverage.csv", index=False)
    raw.to_csv(raw_dir / "estimation_replicates.csv", index=False)
    make_figures(estimation[estimation["design"].str.startswith("N")], raw, lr_frame, counter_frame, pointwise, bootstrap, figures)

    return {
        "elapsed_seconds": time.perf_counter() - start,
        "planned_grid_resolved_cells": int((audit["regime_status"] == "resolved").sum()),
        "planned_grid_total_cells": int(len(audit)),
        "core_replicates": int(sum(int(x["reps"]) for x in config["theorem_aligned_designs"])),
        "bootstrap_rows": int(len(bootstrap)),
    }
