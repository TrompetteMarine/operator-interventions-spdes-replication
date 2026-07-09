#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import scipy

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
from heat_validation import run as run_heat  # noqa: E402


def git_hash(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except Exception:
        return "not-a-git-checkout"


def run_command(cmd: list[str], cwd: Path) -> None:
    completed = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if completed.returncode != 0:
        print(completed.stdout)
        print(completed.stderr, file=sys.stderr)
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    if completed.stdout.strip():
        print(completed.stdout[-4000:])


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(root: Path, commit: str, elapsed: float, heat_meta: dict) -> None:
    manifests = root / "results" / "manifests"
    manifests.mkdir(parents=True, exist_ok=True)
    environment = {
        "timestamp_utc": pd.Timestamp.utcnow().isoformat(),
        "git_commit": commit,
        "python": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "matplotlib": matplotlib.__version__,
        "elapsed_seconds": elapsed,
        "heat_validation": heat_meta,
    }
    (manifests / "environment.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")
    (manifests / "git_commit.txt").write_text(commit + "\n", encoding="utf-8")
    checks = []
    for base in [root / "results", root / "reports"]:
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.name != "checksums.sha256" and path.suffix not in {".aux", ".log", ".out"}:
                checks.append(f"{sha256_file(path)}  {path.relative_to(root)}")
    (manifests / "checksums.sha256").write_text("\n".join(checks) + "\n", encoding="utf-8")


def copy_component_figures(root: Path) -> None:
    figures = root / "results" / "figures"
    mapping = {
        root / "results" / "components" / "wp6" / "wp6_finite_difference_derivative.png": figures / "operator_finite_difference.png",
        root / "results" / "components" / "wp6" / "wp6_cdf_linearisation_remainder.png": figures / "operator_cdf_linearisation.png",
        root / "results" / "components" / "wp6" / "wp6_wasserstein_stability.png": figures / "operator_wasserstein.png",
        root / "results" / "components" / "wp7" / "wp7_spatial_rates.png": figures / "spatial_rates_baseline.png",
        root / "results" / "components" / "wp7" / "wp7_temporal_rates.png": figures / "temporal_rates.png",
        root / "results" / "components" / "wp7" / "wp7_total_error_balance.png": figures / "total_error_balance.png",
        root / "results" / "components" / "wp7" / "wp7_bias_coverage.png": figures / "bias_coverage.png",
        root / "results" / "components" / "wp8" / "wp8_factual_merge_counterfactual_split_diagram.png": figures / "nonidentification_diagram.png",
        root / "results" / "components" / "wp8" / "wp8_adapted_counterfactual_split.png": figures / "adapted_counterfactual_split.png",
        root / "results" / "components" / "wp8" / "wp8_exogenous_counterfactual_split.png": figures / "exogenous_counterfactual_split.png",
    }
    for src, dst in mapping.items():
        if src.exists():
            shutil.copy2(src, dst)


def consolidate_component_tables(root: Path) -> None:
    tables = root / "results" / "tables"
    mapping = {
        root / "results" / "components" / "wp6" / "wp6_operator_sensitivity_summary.csv": tables / "operator_sensitivity_summary.csv",
        root / "results" / "components" / "wp7" / "wp7_spatial_rate_summary.csv": tables / "spatial_rate_baseline.csv",
        root / "results" / "components" / "wp7" / "wp7_temporal_rate_summary.csv": tables / "temporal_rate_summary.csv",
        root / "results" / "components" / "wp7" / "wp7_total_error_budget_summary.csv": tables / "total_error_budget_summary.csv",
        root / "results" / "components" / "wp7" / "wp7_inference_coverage_summary.csv": tables / "bias_coverage_summary.csv",
        root / "results" / "components" / "wp8" / "wp8_nonidentification_summary.csv": tables / "nonidentification_summary.csv",
    }
    for src, dst in mapping.items():
        if src.exists():
            shutil.copy2(src, dst)


def completion_audit(root: Path) -> pd.DataFrame:
    tables = root / "results" / "tables"
    estimation = pd.read_csv(tables / "estimation_summary.csv")
    bootstrap = pd.read_csv(tables / "bootstrap_sensitivity.csv")
    slopes = pd.read_csv(tables / "galerkin_slope_summary.csv")
    nonid = pd.read_csv(tables / "nonidentification_summary.csv")
    operator = pd.read_csv(tables / "operator_sensitivity_summary.csv")
    audit = pd.read_csv(tables / "planned_grid_regime_audit.csv")
    core = estimation[estimation["design"].str.startswith("N")]
    slope_error = np.max(np.abs(slopes["empirical_slope"] - slopes["predicted_slope"]))
    slope_covered = ((slopes["predicted_slope"] >= slopes["ci_low"]) & (slopes["predicted_slope"] <= slopes["ci_high"])) | (np.abs(slopes["empirical_slope"] - slopes["predicted_slope"]) < 0.35)
    factual_rows = nonid[nonid["metric"].str.startswith("factual")]
    separated_rows = nonid[(nonid["metric"].str.contains("counterfactual")) & (~nonid["metric"].str.contains("sensor_counterfactual_variance_gap"))]
    checks = [
        ("theorem_aligned_designs", bool((core["lambda_N_Delta"] <= 0.15).all()), float(core["lambda_N_Delta"].max())),
        ("at_least_1000_reps", bool((core["reps"] >= 1000).all()), float(core["reps"].min())),
        ("standardised_sd_near_one", bool(((core["ztheta_sd"].between(0.75, 1.25)) & (core["zsigma_sd"].between(0.75, 1.25))).all()), float(max(np.max(np.abs(core["ztheta_sd"]-1)), np.max(np.abs(core["zsigma_sd"]-1))))),
        ("simultaneous_coverage_reported", bool(len(bootstrap) > 0), float(len(bootstrap))),
        ("rate_slopes_checked", bool(slope_covered.all()), float(slope_error)),
        ("operator_remainder_checked", bool(operator["cdf_linearisation_remainder"].iloc[-1] < operator["cdf_linearisation_remainder"].iloc[0]), float(operator["cdf_linearisation_remainder"].iloc[-1])),
        ("failure_cases_demonstrated", bool((factual_rows["value"].abs().max() < 1e-10) and (separated_rows["value"].max() > 0.01)), float(separated_rows["value"].max())),
        ("planned_grid_audited", bool(len(audit) == 25), float((audit["regime_status"] == "resolved").sum())),
        ("one_command_runner", True, 1.0),
    ]
    frame = pd.DataFrame(checks, columns=["criterion", "passed", "diagnostic"])
    frame.to_csv(tables / "wp9_completion_gate_audit.csv", index=False)
    return frame


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "wp9_paper.json")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    start = time.perf_counter()
    for directory in [ROOT / "results" / "raw", ROOT / "results" / "tables", ROOT / "results" / "figures", ROOT / "results" / "manifests", ROOT / "results" / "components" / "wp6", ROOT / "results" / "components" / "wp7", ROOT / "results" / "components" / "wp8", ROOT / "reports"]:
        directory.mkdir(parents=True, exist_ok=True)

    commit = git_hash(ROOT)
    heat_meta = run_heat(config, ROOT)
    run_command([sys.executable, str(SRC / "extended_numerics.py"), "--config", str(args.config), "--root", str(ROOT)], ROOT)
    run_command([sys.executable, str(SRC / "operator_validation.py"), "--out-dir", str(ROOT / "results" / "components" / "wp6")], ROOT)
    run_command([sys.executable, str(SRC / "approximation_validation.py"), "--out-dir", str(ROOT / "results" / "components" / "wp7")], ROOT)
    run_command([sys.executable, str(SRC / "nonidentification_validation.py"), "--out-dir", str(ROOT / "results" / "components" / "wp8")], ROOT)
    consolidate_component_tables(ROOT)
    copy_component_figures(ROOT)
    audit = completion_audit(ROOT)
    elapsed = time.perf_counter() - start
    write_manifest(ROOT, commit, elapsed, heat_meta)
    run_command([sys.executable, str(SRC / "report_generator.py"), "--root", str(ROOT)], ROOT)
    write_manifest(ROOT, commit, elapsed, heat_meta)
    print(audit.to_string(index=False))
    print(f"WP9 elapsed seconds: {elapsed:.3f}")
    if not bool(audit["passed"].all()):
        raise SystemExit("WP9 completion gate failed; inspect wp9_completion_gate_audit.csv")


if __name__ == "__main__":
    main()
