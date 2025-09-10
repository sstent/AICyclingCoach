# Multi-stage build for container-first development
FROM python:3.11-slim-bullseye AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies for building
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim-bullseye AS runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install runtime system dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create entrypoint script for migration handling
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Run database migrations synchronously\n\
echo "Running database migrations..."\n\
python -m alembic upgrade head\n\
\n\
# Verify migration success\n\
echo "Verifying migration status..."\n\
python -m alembic current\n\
\n\
# Start the application\n\
echo "Starting application..."\n\
exec "$@"' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Create non-root user and logs directory
RUN useradd -m appuser && \
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app
USER appuser

# Expose application port
EXPOSE 8000

# Use entrypoint for migration automation
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]