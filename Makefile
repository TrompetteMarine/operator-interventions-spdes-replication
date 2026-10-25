PYTHON ?= python3
export PYTHONPATH := replication/python

.PHONY: verify reproduce-preview reproduce-standard reproduce-publication reproduce-paper sweeps regime-scan paper

verify:
	$(PYTHON) -m pytest replication/python/tests -q

reproduce-preview:
	$(PYTHON) replication/python/scripts/run_all.py preview

reproduce-standard:
	$(PYTHON) replication/python/scripts/run_all.py standard

reproduce-publication:
	$(PYTHON) replication/python/scripts/run_all.py publication

# End-to-end validation pipeline (generates the paper's data figures).
reproduce-paper:
	cd replication/validation && $(PYTHON) run_wp9.py --config config/wp9_paper.json
	cp replication/validation/results/figures/*.png paper/figures/ 2>/dev/null || true

# Additional experiment sweeps (variance curve, coverage sweep, test power).
sweeps:
	$(PYTHON) replication/scripts/extra_sweeps.py

# Regime scan: LAN-aligned vs fixed-resolution vs under-resolved ladders
# (paper Table "Regime scan"; writes results/tables/regime_scan.csv).
regime-scan:
	$(PYTHON) replication/scripts/regime_scan.py

# Static Lean-integrity audit: fails on sorry/admit/sorryAx or any axiom
# declaration in the formalization sources. (Full `lake build` requires the
# pinned toolchain; run it in the formalization/ directory for kernel checks.)
lean-audit:
	@! grep -rnE '(^|[^a-zA-Z])(sorry|admit|sorryAx)([^a-zA-Z]|$$)' formalization/RequestProject/*.lean || (echo "FORBIDDEN TOKEN FOUND" && exit 1)
	@! grep -rnE '^[[:space:]]*axiom ' formalization/RequestProject/*.lean || (echo "PROJECT AXIOM FOUND" && exit 1)
	@echo "lean-audit: no sorry/admit/sorryAx, no project axioms in $$(ls formalization/RequestProject/*.lean | wc -l) files"

# Verify that committed result files match their recorded SHA-256 manifest.
verify-manifest:
	@$(PYTHON) replication/scripts/verify_manifest.py

paper:
	cd paper && $(PYTHON) build_supplement.py && \
	pdflatex -interaction=nonstopmode paper_merged && bibtex paper_merged && \
	pdflatex -interaction=nonstopmode paper_merged && pdflatex -interaction=nonstopmode paper_merged
