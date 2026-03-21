.PHONY: setup run test eval lint format validate scaffold preflight

## Setup — install dependencies and configure
setup:
	bash scripts/setup.sh

## Run — start the interactive agent platform
run:
	uv run --package router-agent python -m router.main

## Test — run all tests
test:
	uv run pytest tests/ agents/*/tests/ -v --no-header

## Eval — run agent quality evaluations (requires Azure credentials)
eval:
	uv run pytest evals/ -m eval -v --no-header

## Lint — check code style
lint:
	uv run ruff check .

## Format — auto-format code
format:
	uv run ruff format .

## Validate — check all agent configs and tools
validate:
	uv run python -m agent_core.validate

## Scaffold — create a new agent (usage: make scaffold name=my-agent desc="What it does")
scaffold:
	uv run python -m agent_core.scaffold $(name) --description "$(desc)"

## Preflight — check Azure prerequisites
preflight:
	uv run python scripts/preflight.py

## DevUI — browser-based agent testing
devui:
	uv run devui --port 8080

## Docker — run in containers
docker:
	docker compose up --build
