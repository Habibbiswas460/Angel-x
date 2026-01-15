# Angel-X Makefile
# Common development and deployment commands

.PHONY: help install dev prod test lint format clean docker deploy

help:
	@echo "Angel-X Development Commands"
	@echo "============================"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install       - Install dependencies"
	@echo "  make dev          - Setup development environment"
	@echo "  make prod         - Setup production environment"
	@echo ""
	@echo "Development:"
	@echo "  make run          - Run development server"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linting checks"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean temporary files"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"
	@echo "  make docker-up    - Start Docker Compose"
	@echo "  make docker-down  - Stop Docker Compose"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy       - Deploy to production"
	@echo "  make health       - Check application health"

install:
	python3 -m venv venv
	source venv/bin/activate && pip install -r requirements.txt

dev:
	bash setup.sh dev

prod:
	bash setup.sh prod

run:
	source venv/bin/activate && python main.py

test:
	source venv/bin/activate && pytest tests/ -v --cov=src

lint:
	source venv/bin/activate && \
		pylint src/ && \
		flake8 src/ && \
		mypy src/

format:
	source venv/bin/activate && \
		black src/ tests/ && \
		isort src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage

docker-build:
	docker build -t angel-x:latest .

docker-run:
	docker run -it --env-file .env angel-x:latest

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

deploy:
	bash production-deploy.sh

health:
	@curl -s http://localhost:5000/health | python -m json.tool || echo "Application not running"

.DEFAULT_GOAL := help
