#!/usr/bin/env python3
"""Additional experiment sweeps beyond the profile runs.

Outputs (results/sweeps/): estimation sweep over a finer N-grid on the
theorem-aligned path n = 80 N^2 (standardised sd, bias, KS-normality
p-values, empirical theta-sigma correlation), the analytic post-intervention
variance monotonicity curve across intervention values and modes, and a
figure per table. Seeded; writes a JSON manifest with environment, runtime,
and SHA-256 checksums.

Usage: extra_sweeps.py [--chunk k]   (k in 0..3: one estimation design per
call; --chunk -1 or no flag: everything incl. aggregation)
"""
from __future__ import annotations
import argparse, hashlib, json, platform, time
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

from causal_spdes.core import heat_eigenvalues, noise_loadings
from causal_spdes.likelihood import simulate_exact_ou, profile_mle
from causal_spdes.targets import integrated_mode_variance

ROOT = Path(__file__).resolve().parents[1] / "results" / "sweeps"
SEED = 20260709
THETA, SIGMA, T, BETA = 0.7, 0.8, 1.0, 0.75
DESIGNS = [(4, 1280), (6, 2880), (8, 5120), (12, 11520)]  # n = 80 N^2
REPS = 150


def run_design(idx: int) -> None:
    N, n = DESIGNS[idx]
    lam = heat_eigenvalues(N)
    q = noise_loadings(lam, BETA)
    Lam = float(lam.sum())
    th, sg = [], []
    for r in range(REPS):
        y = simulate_exact_ou(THETA, SIGMA, lam, q, n, T,
                              seed=SEED + 100000 * N + r)
        a, b = profile_mle(y, lam, q, T)
        th.append(a); sg.append(b)
    th, sg = np.array(th), np.array(sg)
    zt = np.sqrt(Lam) * (th - THETA) / np.sqrt(2 * THETA / T)
    zs = np.sqrt(N * n) * (sg - SIGMA) / (SIGMA / np.sqrt(2))
    row = {
        "N": N, "n": n, "reps": REPS, "lambda_N_dt": float(lam[-1] * T / n),
        "theta_bias": float(th.mean() - THETA),
        "sigma_bias": float(sg.mean() - SIGMA),
        "z_theta_sd": float(zt.std(ddof=1)),
        "z_sigma_sd": float(zs.std(ddof=1)),
        "z_theta_skew": float(stats.skew(zt)),
        "ks_p_theta": float(stats.kstest(zt, "norm").pvalue),
        "ks_p_sigma": float(stats.kstest(zs, "norm").pvalue),
        "corr_z_theta_sigma": float(np.corrcoef(zt, zs)[0, 1]),
    }
    (ROOT / "tables").mkdir(parents=True, exist_ok=True)
    pd.DataFrame([row]).to_csv(ROOT / "tables" / f"estimation_N{N}.csv",
                               index=False)
    print(f"design {N},{n}: z_sd=({row['z_theta_sd']:.3f},"
          f"{row['z_sigma_sd']:.3f}) ks_p=({row['ks_p_theta']:.3f},"
          f"{row['ks_p_sigma']:.3f}) corr={row['corr_z_theta_sigma']:.3f}")


def aggregate() -> None:
    (ROOT / "figures").mkdir(parents=True, exist_ok=True)
    start = time.time()
    parts = sorted((ROOT / "tables").glob("estimation_N*.csv"))
    frame = pd.concat([pd.read_csv(p) for p in parts]).sort_values("N")
    frame.to_csv(ROOT / "tables" / "estimation_sweep.csv", index=False)

    fig, ax = plt.subplots(1, 3, figsize=(12.5, 3.6))
    ax[0].plot(frame.N, frame.z_theta_sd, "o-", label=r"$\mathrm{sd}(Z_\theta)$")
    ax[0].plot(frame.N, frame.z_sigma_sd, "s-", label=r"$\mathrm{sd}(Z_\sigma)$")
    ax[0].axhline(1.0, ls="--", c="k", lw=.8)
    ax[0].set_xlabel("N"); ax[0].legend()
    ax[0].set_title("information-standardised sd")
    ax[1].plot(frame.N, frame.ks_p_theta, "o-", label=r"KS $p$ ($Z_\theta$)")
    ax[1].plot(frame.N, frame.ks_p_sigma, "s-", label=r"KS $p$ ($Z_\sigma$)")
    ax[1].axhline(0.05, ls="--", c="k", lw=.8)
    ax[1].set_xlabel("N"); ax[1].legend()
    ax[1].set_title("normality diagnostics")
    ax[2].plot(frame.N, frame.corr_z_theta_sigma, "o-")
    ax[2].axhline(0.0, ls="--", c="k", lw=.8)
    ax[2].set_xlabel("N")
    ax[2].set_title(r"empirical $\mathrm{corr}(Z_\theta,Z_\sigma)$")
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "estimation_sweep.png", dpi=170)
    plt.close(fig)

    # analytic variance monotonicity across intervention values and modes
    rates = np.linspace(0.3, 2.4, 60)
    lam = heat_eigenvalues(4)
    q = noise_loadings(lam, BETA)
    rows = []
    fig, axv = plt.subplots(figsize=(6.6, 4.0))
    for k in range(4):
        v = np.array([integrated_mode_variance(a * lam[k], SIGMA, q[k], T)
                      for a in rates])
        axv.plot(rates, v / v[0], label=f"mode k={k+1}")
        rows += [{"a": float(a), "mode": k + 1, "variance": float(x)}
                 for a, x in zip(rates, v)]
    axv.set_xlabel(r"intervention value $a$")
    axv.set_ylabel("integrated-functional variance (normalised)")
    axv.legend(); fig.tight_layout()
    fig.savefig(ROOT / "figures" / "variance_monotonicity.png", dpi=170)
    plt.close(fig)
    pd.DataFrame(rows).to_csv(ROOT / "tables" / "variance_monotonicity.csv",
                              index=False)

    checks = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(ROOT.rglob("*")) if p.is_file()
              and p.suffix in {".csv", ".png"}}
    manifest = {
        "seed": SEED, "designs": DESIGNS, "reps": REPS,
        "theta": THETA, "sigma": SIGMA, "horizon": T, "beta": BETA,
        "python": platform.python_version(),
        "numpy": np.__version__, "pandas": pd.__version__,
        "aggregate_elapsed_s": round(time.time() - start, 2),
        "sha256": checks,
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(frame.to_string(index=False))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--chunk", type=int, default=-1)
    a = p.parse_args()
    if 0 <= a.chunk < len(DESIGNS):
        run_design(a.chunk)
    else:
        for i in range(len(DESIGNS)):
            run_design(i)
        aggregate()
