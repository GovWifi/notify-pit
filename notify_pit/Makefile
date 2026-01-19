IMAGE_NAME := notify-pit
PWD := $(shell pwd)

.PHONY: all build test run clean lint format localuitest

all: test

# Build the images using Docker Compose
build:
	docker compose build

# Run the application (Production mode, accessible at localhost:8000)
run:
	docker compose up app

# Run all tests (unit+UI):
test:
	docker compose up -d app
	docker compose run --rm tests pytest --browser chromium --cov=app --cov-report=xml:/app/tests/coverage.xml tests/
	docker compose down

# Usage: make localuitest
# Runs the UI tests locally against a manually started service
# Install local deps if needed (optional, safe to remove if already installed)
# pip install -r requirements-dev.txt
# playwright install chromium
localuitest:
	@echo "Waiting for Notify.pit to be ready at http://localhost:8000..."
	@bash -c 'while ! curl -s http://localhost:8000/healthcheck > /dev/null; do sleep 1; done'
	@echo "Service is up! Running UI tests..."
	# Run the tests visually
	pytest tests/test_ui.py --headed --slowmo 1000

# Check code style (used in CI)
lint:
	ruff check .
	ruff format --check .

# Fix code style automatically (run this locally)
format:
	ruff check --fix .
	ruff format .

# Clean up containers and images
clean:
	docker compose down --rmi local