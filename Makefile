PYTHON ?= python3
export PYTHONPATH := replication/python

.PHONY: verify reproduce-preview reproduce-standard reproduce-publication reproduce-paper sweeps paper

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

paper:
	cd paper && $(PYTHON) build_supplement.py && \
	pdflatex -interaction=nonstopmode paper_merged && bibtex paper_merged && \
	pdflatex -interaction=nonstopmode paper_merged && pdflatex -interaction=nonstopmode paper_merged
