.PHONY: help install test lint format clean deploy docker-build docker-run

help:
	@echo "RFM-LDE Multiagent - Available Commands"
	@echo "======================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          Install dependencies"
	@echo "  make setup            Full setup (install + config)"
	@echo ""
	@echo "Development:"
	@echo "  make test             Run all tests"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-cov         Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run code linters (flake8, mypy)"
	@echo "  make format           Auto-format code (black, isort)"
	@echo "  make clean            Remove build artifacts"
	@echo ""
	@echo "Production:"
	@echo "  make deploy           Deploy Lambda function"
	@echo "  make docker-build     Build Docker image"
	@echo "  make docker-run       Run Docker container locally"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs             Generate API documentation"

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

setup: install
	cp .env.example .env
	@echo "✅ Setup complete. Update .env with your AWS credentials"

test:
	pytest -v --tb=short --cov=src --cov-report=html

test-unit:
	pytest tests/unit -v --tb=short

test-integration:
	pytest tests/integration -v --tb=short

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term-missing
	@echo "Coverage report: htmlcov/index.html"

lint:
	flake8 src tests --max-line-length=100
	mypy src --ignore-missing-imports

format:
	black src tests
	isort src tests

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name "htmlcov" -exec rm -r {} +
	find . -type f -name ".coverage" -delete

deploy:
	@echo "Deploying Lambda function..."
	cd src/lambdas/rfm_lde_multiagente && \
	pip install -r requirements.txt -t package/ && \
	cp -r ../../agents package/src/ && \
	cd package && zip -r ../lambda_function.zip . && \
	aws lambda update-function-code \
		--function-name rfm-lde-multiagente-dev \
		--zip-file fileb://../lambda_function.zip \
		--region us-east-1
	@echo "✅ Deployment complete"

docker-build:
	docker build -t rfm-lde-multiagent:latest .

docker-run:
	docker run -p 8000:8000 \
		--env-file .env \
		rfm-lde-multiagent:latest

docs:
	@echo "Generating API documentation..."
	sphinx-build -b html docs/source docs/build
	@echo "Docs generated: docs/build/index.html"

.DEFAULT_GOAL := help
