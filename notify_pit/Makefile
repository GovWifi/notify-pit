IMAGE_NAME := notify-pit
PWD := $(shell pwd)

.PHONY: all build test clean

# Default target: run tests
all: test

# Build the Docker image
# Docker's caching ensures this is fast/skipped if nothing has changed.
build:
	docker build -t $(IMAGE_NAME) .

# Run the tests with coverage
# 1. Depends on 'build' to ensure the image and dependencies are ready.
# 2. Mounts local '/app' so code changes work immediately without a full rebuild.
# 3. Mounts local '/tests' so you can add tests without rebuilding.
test: build
	docker run --rm \
		-v "$(PWD)/tests:/app/tests" \
		-v "$(PWD)/app:/app/app" \
		$(IMAGE_NAME) \
		pytest --cov=app tests/

# Stop and remove the image (optional cleanup)
clean:
	docker rmi $(IMAGE_NAME) || true

