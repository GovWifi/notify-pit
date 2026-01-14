IMAGE_NAME := notify-pit
PWD := $(shell pwd)

.PHONY: all build test run clean

all: test

# Build the images using Docker Compose
build:
	docker compose build

# Run the application (Production mode, accessible at localhost:8000)
run:
	docker compose up app

# Run the test suite
# 1. Start the 'app' service in the background (-d)
# 2. Run the 'tests' service to execute pytest
# 3. Stop containers after tests finish

# Allow passing extra arguments to pytest (e.g. make test ARGS="--headed")
ARGS ?=

test:
	docker compose up -d app
	# We override the default command to include $(ARGS)
	docker compose run --rm tests pytest --browser chromium $(ARGS)
	docker compose down

# Clean up containers and images
clean:
	docker compose down --rmi local