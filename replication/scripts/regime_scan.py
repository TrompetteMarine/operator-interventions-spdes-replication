#!/usr/bin/env python3
"""Regime scan: asymptotically aligned vs fixed-resolution vs under-resolved designs.

Referee-driven experiment (report item 2): the publication designs n = 80 N^2
hold the resolution lambda_N * Delta_n = pi^2 T / 80 ~ 0.123 constant, so they
illustrate finite-sample behaviour at a fixed small resolution but do not test
the asymptotic regime lambda_N * Delta_n -> 0 of Theorem 5.1.  This script runs
three design ladders for the 1-d Dirichlet heat equation:

  aligned    n = round(80 N^2 log N / log 5)  -> n/N^2 diverges (lam*Dt -> 0)
  fixed      n = 80 N^2                       -> lam*Dt = 0.123 constant
  violating  n = 20 N                         -> lam*Dt diverges (under-resolved)

and reports, per design, the information-standardised moments
  Z_theta = sqrt(Lambda_N) (theta_hat - theta_0) / sqrt(2 theta_0 / T),
  Z_sigma = sqrt(N n)     (sigma_hat - sigma_0) / (sigma_0 / sqrt 2),
their empirical means, standard deviations, correlation, and the fraction of
replications in which the scale clamp of the corrected constrained profile
(Proposition 9.13) is active.  Monte Carlo standard error for the reported
standard deviations with R replications is approximately sd/sqrt(2(R-1)).

Simulation uses the exact OU transition of causal_spdes.likelihood, vectorised
across replications (identical recursion, seeded); estimation calls
causal_spdes.likelihood.profile_mle with the corrected constrained profile.

Output: results/tables/regime_scan.csv and a printed table.
"""
from __future__ import annotations
import json, math, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from causal_spdes.core import heat_eigenvalues, noise_loadings  # noqa: E402
from causal_spdes.likelihood import transition_parameters, profile_mle  # noqa: E402

CONFIG = json.loads((ROOT / "config" / "profiles.json").read_text())["publication"]
THETA, SIGMA, T, BETA, SEED = (CONFIG["theta"], CONFIG["sigma"], CONFIG["horizon"],
                               CONFIG["beta"], CONFIG["seed"])
REPS = 300
SIGMA_BOUNDS = (0.2, 3.2)          # compact scale interval; sigma_0 = 0.8 interior
NS = [5, 10, 20]

def ladders():
    out = []
    for N in NS:
        out.append(("aligned", N, int(round(80 * N * N * math.log(N) / math.log(5)))))
    for N in NS:
        out.append(("fixed", N, 80 * N * N))
    for N in NS:
        out.append(("violating", N, 20 * N))
    return out

def simulate_batch(theta, sigma, lam, q, n_times, horizon, reps, seed):
    """Batched exact OU recursion: y_{j+1} = rho y_j + sqrt(var) Z, Z ~ N(0, I).

    Same transition as causal_spdes.likelihood.simulate_exact_ou, vectorised
    over replications; accumulates the sufficient statistics per replication.
    """
    rng = np.random.default_rng(seed)
    dt = horizon / n_times
    rho, var = transition_parameters(theta, sigma, lam, q, dt)
    sd = np.sqrt(var)
    y = np.zeros((reps, len(lam)))
    sxx = np.zeros_like(y); sxy = np.zeros_like(y); syy = np.zeros_like(y)
    for _ in range(n_times):
        nxt = rho * y + sd * rng.standard_normal(y.shape)
        sxx += y * y; sxy += y * nxt; syy += nxt * nxt
        y = nxt
    return sxx, sxy, syy

class _Stats:
    """Adapter so profile_mle can consume precomputed sufficient statistics."""
    pass

def mle_from_stats(sxx, sxy, syy, lam, q, n_times, horizon):
    # profile_mle expects a path; feed it a 2-row surrogate carrying the exact
    # sufficient statistics is not possible, so replicate its objective here
    # by monkey-free reuse: build a minimal shim via the module internals.
    from scipy.optimize import minimize_scalar
    n_modes = len(lam); dt = horizon / n_times
    lo2, hi2 = SIGMA_BOUNDS[0] ** 2, SIGMA_BOUNDS[1] ** 2
    def clamp(v): return min(max(v, lo2), hi2)
    def objective(theta):
        rho = np.exp(-theta * lam * dt)
        h = -np.expm1(-2.0 * theta * lam * dt) / (2.0 * theta * lam)
        rss = np.sum((syy - 2 * rho * sxy + rho * rho * sxx) / (q * q * h))
        s2 = rss / (n_modes * n_times)
        v = clamp(s2)
        return n_modes * n_times * (np.log(v) + s2 / v) + n_times * np.sum(np.log(q * q * h))
    res = minimize_scalar(objective, bounds=(0.05, 3.0), method="bounded",
                          options={"xatol": 1e-10})
    th = float(res.x)
    rho = np.exp(-th * lam * dt)
    h = -np.expm1(-2 * th * lam * dt) / (2 * th * lam)
    rss = np.sum((syy - 2 * rho * sxy + rho * rho * sxx) / (q * q * h))
    s2 = rss / (n_modes * n_times)
    return th, float(np.sqrt(clamp(s2))), (s2 < lo2 or s2 > hi2)

def main():
    (ROOT / "results" / "tables").mkdir(parents=True, exist_ok=True)
    rows = []
    t0 = time.time()
    for fam_i, (family, N, n) in enumerate(ladders()):
        lam = heat_eigenvalues(N); q = noise_loadings(lam, BETA)
        Lambda = float(np.sum(lam))
        lam_dt = float(lam[-1]) * T / n
        sxx, sxy, syy = simulate_batch(THETA, SIGMA, lam, q, n, T, REPS,
                                       SEED + 7_000_000 * (fam_i + 1))
        th = np.empty(REPS); sg = np.empty(REPS); clamped = 0
        for r in range(REPS):
            a, b, hit = mle_from_stats(sxx[r], sxy[r], syy[r], lam, q, n, T)
            th[r], sg[r] = a, b; clamped += int(hit)
        zt = np.sqrt(Lambda) * (th - THETA) / np.sqrt(2 * THETA / T)
        zs = np.sqrt(N * n) * (sg - SIGMA) / (SIGMA / np.sqrt(2))
        rows.append({
            "family": family, "N": N, "n": n, "reps": REPS,
            "lamN_dt": round(lam_dt, 4),
            "mean_Z_theta": round(float(np.mean(zt)), 3),
            "sd_Z_theta": round(float(np.std(zt, ddof=1)), 3),
            "mean_Z_sigma": round(float(np.mean(zs)), 3),
            "sd_Z_sigma": round(float(np.std(zs, ddof=1)), 3),
            "corr": round(float(np.corrcoef(zt, zs)[0, 1]), 3),
            "clamp_active_frac": round(clamped / REPS, 4),
        })
        print(f"[{time.time()-t0:7.1f}s] {family:9s} N={N:2d} n={n:6d} done")
    frame = pd.DataFrame(rows)
    out = ROOT / "results" / "tables" / "regime_scan.csv"
    frame.to_csv(out, index=False)
    print(frame.to_string(index=False))
    print(f"MC s.e. for sd columns ~ 1/sqrt(2(R-1)) = {1/np.sqrt(2*(REPS-1)):.3f}")
    print("written:", out)

if __name__ == "__main__":
    main()
