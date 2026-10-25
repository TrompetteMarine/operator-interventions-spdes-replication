#!/usr/bin/env python3
"""Verify committed result files against their recorded SHA-256 manifest.

Usage:
  python3 replication/scripts/verify_manifest.py            # verify
  python3 replication/scripts/verify_manifest.py --update   # (re)record

Exit status is non-zero on any mismatch or missing file, so `make
verify-manifest` fails on drift between committed results and the manifest.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "results" / "logs" / "results_manifest.json"
TRACKED = [
    "results/tables/regime_scan.csv",
    "results/tables/estimation_summary.csv",
    "results/tables/nonidentification_summary.csv",
]

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()

def main() -> int:
    update = "--update" in sys.argv[1:]
    tracked = [(rel, ROOT / rel) for rel in TRACKED]
    if update:
        entries = {rel: sha256(p) for rel, p in tracked if p.exists()}
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(json.dumps(entries, indent=2) + "\n")
        print(f"recorded {len(entries)} entries -> {MANIFEST}")
        return 0
    if not MANIFEST.exists():
        print("no manifest recorded; run with --update after generating results")
        return 1
    entries = json.loads(MANIFEST.read_text())
    status = 0
    for rel, expected in entries.items():
        p = ROOT / rel
        if not p.exists():
            print(f"MISSING  {rel}")
            status = 1
            continue
        actual = sha256(p)
        ok = actual == expected
        print(f"{'OK      ' if ok else 'MISMATCH'} {rel}")
        if not ok:
            status = 1
    return status

if __name__ == "__main__":
    raise SystemExit(main())
