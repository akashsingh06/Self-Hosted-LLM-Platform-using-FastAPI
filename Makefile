.PHONY: help install dev test lint format docker-up docker-down deploy

help:
	@echo "Available commands:"
	@echo "  install     Install dependencies"
	@echo "  dev         Run development server"
	@echo "  test        Run tests"
	@echo "  lint        Run linters"
	@echo "  format      Format code"
	@echo "  docker-up   Start all services with Docker"
	@echo "  docker-down Stop all services"
	@echo "  deploy      Deploy to production"

install:
	pip install -e .[dev,monitoring]

dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --cov=src --cov-report=html

lint:
	flake8 src/
	mypy src/
	black --check src/

format:
	black src/
	isort src/

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

deploy:
	@echo "Deploying to production..."
	git pull origin main
	docker-compose build
	docker-compose up -d
	docker system prune -f
