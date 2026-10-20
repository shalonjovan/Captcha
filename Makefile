PYTHON ?= python
DIST_DIR := dist

.PHONY: install install-dev test coverage lint format format-check docs docs-serve build check gallery clean

install:
	$(PYTHON) -m pip install -e .

install-dev:
	$(PYTHON) -m pip install -e ".[dev,docs]"

test:
	$(PYTHON) -m pytest

coverage:
	$(PYTHON) -m pytest --cov=captcha_forge --cov-report=term-missing --cov-report=html

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

format:
	$(PYTHON) -m ruff format .
	$(PYTHON) -m ruff check --fix .

docs:
	$(PYTHON) -m mkdocs build --strict

docs-serve:
	$(PYTHON) -m mkdocs serve

build:
	rm -rf $(DIST_DIR)
	$(PYTHON) -m build
	$(PYTHON) -m twine check $(DIST_DIR)/*

check: lint test docs build

gallery:
	$(PYTHON) scripts/generate_gallery.py

clean:
	rm -rf $(DIST_DIR) build htmlcov .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
