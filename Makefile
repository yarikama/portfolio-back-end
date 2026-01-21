SHELL := /bin/bash

# Variables definitions
# -----------------------------------------------------------------------------

ifeq ($(TIMEOUT),)
TIMEOUT := 60
endif

ifeq ($(MODEL_PATH),)
MODEL_PATH := ./ml/model/
endif

ifeq ($(MODEL_NAME),)
MODEL_NAME := model.pkl
endif

# Target section and Global definitions
# -----------------------------------------------------------------------------
.PHONY: all clean test install run deploy down lint format hash logs shell rebuild

all: clean install test

install: generate_dot_env
	uv sync --all-extras

test:
	uv run pytest -vv --show-capture=all

run:
	PYTHONPATH=app/ uv run uvicorn main:app --reload --host 0.0.0.0 --port 8080

lint:
	uv run ruff check app/

format:
	uv run ruff format app/
	uv run ruff check --fix app/

hash:
	@read -p "Enter password: " pwd && \
	uv run python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('$$pwd'))"

deploy: generate_dot_env
	docker-compose build
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f app

shell:
	docker-compose exec app bash

rebuild:
	docker-compose build --no-cache
	docker-compose up -d

generate_dot_env:
	@if [[ ! -e .env ]]; then \
		cp .env.example .env; \
	fi

clean:
	@find . -name '*.pyc' -exec rm -rf {} \;
	@find . -name '__pycache__' -exec rm -rf {} \;
	@find . -name 'Thumbs.db' -exec rm -rf {} \;
	@find . -name '*~' -exec rm -rf {} \;
	rm -rf .cache
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
	rm -rf htmlcov
	rm -rf .tox/
	rm -rf docs/_build
