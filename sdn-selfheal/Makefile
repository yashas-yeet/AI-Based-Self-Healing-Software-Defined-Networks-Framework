# Makefile for sdn-selfheal

PYTHON ?= python3
VENV ?= .venv
PIP ?= $(VENV)/bin/pip
PYTEST ?= $(VENV)/bin/pytest

.PHONY: help setup venv clean test smoke-all lint

help:
	@echo "Available targets:"
	@echo "  setup        - Initialize Python virtual environment and install dependencies"
	@echo "  test         - Run all test suites"
	@echo "  smoke-all    - Run smoke tests across all phases"
	@echo "  clean        - Clean temporary files, caches, and Mininet interfaces"
	@echo "  run-matrix   - Execute full experimental matrix"

venv:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt

setup: venv

clean:
	rm -rf $(VENV) .pytest_cache __pycache__ */__pycache__ */*/__pycache__
	rm -rf results/raw/* results/processed/* results/figures/*
	sudo mn -c 2>/dev/null || true

test:
	$(PYTEST) -v tests/

analyze:
	$(VENV)/bin/python3 analysis/run_full_analysis.py

run-matrix:
	$(VENV)/bin/python3 experiments/run_matrix.py --seeds 10
	$(MAKE) analyze
