IMAGE_NAME := notify-pit
PWD := $(shell pwd)

.PHONY: all build test run clean

# Default target: run tests
all: test

# Build the Docker image
# Docker's caching ensures this is fast/skipped if nothing has changed.
build:
	docker build -t $(IMAGE_NAME) .

# Run the service locally on port 8000
# Mounts 'app/' so code changes are reflected immediately (Hot Reload)
run: build
	docker run --rm \
		-p 8000:8000 \
		-v "$(PWD)/app:/app/app" \
		$(IMAGE_NAME)

# Run the tests with coverage
# Mounts 'app/' and 'tests/' so you can test latest changes instantly
test: build
	docker run --rm \
		-v "$(PWD)/tests:/app/tests" \
		-v "$(PWD)/app:/app/app" \
		$(IMAGE_NAME) \
		pytest --cov=app tests/

# Stop and remove the image (optional cleanup)
clean:
	docker rmi $(IMAGE_NAME) || true