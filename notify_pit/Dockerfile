# ==========================================
# Stage 1: Production Image (Small, Fast)
# ==========================================
FROM python:3.12-slim as production

WORKDIR /app

RUN groupadd -g 1009 docker && \
    useradd -u 1009 -g docker -d /app -s /bin/bash docker && \
    chown -R docker:docker /app

# Install production dependencies
COPY --chown=docker:docker requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=docker:docker ./app /app/app
COPY --chown=docker:docker alembic.ini /app/alembic.ini
COPY --chown=docker:docker alembic /app/alembic

USER docker

# Default command for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


# ==========================================
# Stage 2: Test Runner (Includes Browsers)
# ==========================================
FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy as test

WORKDIR /app

RUN groupadd -g 1009 docker && \
    useradd -u 1009 -g docker -d /app -s /bin/bash docker && \
    chown -R docker:docker /app

COPY --chown=docker:docker requirements.txt .
COPY --chown=docker:docker requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Install testing-specific dependencies
RUN pip install pytest-playwright

# Copy the rest of the project (including tests)
COPY --chown=docker:docker . .

USER docker

# Default command to run tests
CMD ["pytest"]