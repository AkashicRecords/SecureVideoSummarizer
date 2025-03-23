.PHONY: help clean test lint format version-bump-patch version-bump-minor version-bump-major install-dev docs

PYTHON = python
PIP = pip
PYTEST = pytest
FLAKE8 = flake8
BLACK = black
ISORT = isort
BUMPVERSION = bump2version
SPHINX = sphinx-build

help:
	@echo "Available commands:"
	@echo "  make clean            - Remove build artifacts and cache files"
	@echo "  make test             - Run tests with pytest"
	@echo "  make coverage         - Run tests with coverage report"
	@echo "  make lint             - Run code linting"
	@echo "  make format           - Format code with black and isort"
	@echo "  make version-patch    - Bump patch version (0.0.x)"
	@echo "  make version-minor    - Bump minor version (0.x.0)"
	@echo "  make version-major    - Bump major version (x.0.0)"
	@echo "  make install-dev      - Install development dependencies"
	@echo "  make docs             - Generate documentation"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .tox/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

test:
	$(PYTEST) -v tests/

coverage:
	$(PYTEST) --cov=app tests/ --cov-report=term --cov-report=html

lint:
	$(FLAKE8) app/ tests/
	$(PYTHON) -m mypy app/ tests/
	$(PYTHON) -m bandit -r app/

format:
	$(BLACK) app/ tests/
	$(ISORT) app/ tests/

version-patch:
	$(BUMPVERSION) patch

version-minor:
	$(BUMPVERSION) minor

version-major:
	$(BUMPVERSION) major

install-dev:
	$(PIP) install -r requirements.dev.txt
	pre-commit install

docs:
	mkdir -p docs/build
	$(SPHINX) docs/source docs/build/html 