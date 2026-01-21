# ==========================================
# Stage 1: Production Image (Small, Fast)
# ==========================================
FROM python:3.12-slim as production

WORKDIR /app

# Install production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app/app
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic

# Default command for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


# ==========================================
# Stage 2: Test Runner (Includes Browsers)
# ==========================================
FROM mcr.microsoft.com/playwright/python:v1.57.0-jammy as test

WORKDIR /app

COPY requirements.txt .
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Install testing-specific dependencies
RUN pip install pytest-playwright

# Copy the rest of the project (including tests)
COPY . .

# Default command to run tests
CMD ["pytest"]