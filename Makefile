.PHONY: test lint format mypy install virtual_env

virtual_env:
	@echo "Creating/ensuring virtual environment..."
	uv venv || true # Using || true to make it idempotent

install:
	@echo "Installing dependencies..."
	uv pip install -r pyproject.toml

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

mypy:
	mypy --explicit-package-bases --namespace-packages expense_manager stream_consumer xcnt

