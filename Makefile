.PHONY: up down test lint format ruff black isort mypy

up:
	docker compose -f infra/docker-compose.yml --env-file infra/.env.example up -d --build

down:
	docker compose -f infra/docker-compose.yml --env-file infra/.env.example down -v

test:
	poetry run pytest -q

ruff:
	poetry run ruff check .

black:
	poetry run black --check .

isort:
	poetry run isort --check-only .

mypy:
	poetry run mypy .

lint: ruff black isort mypy

format:
	poetry run ruff check --fix . || true
	poetry run isort .
	poetry run black .

