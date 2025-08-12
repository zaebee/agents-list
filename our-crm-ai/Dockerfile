# AI Project Manager - Production Docker Image
# Multi-stage build for optimized production deployment

# Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    FLASK_ENV=production \
    GUNICORN_WORKERS=4 \
    GUNICORN_THREADS=2 \
    GUNICORN_TIMEOUT=60

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r aipm \
    && useradd -r -g aipm aipm

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create application directories
RUN mkdir -p /app/logs /app/data && \
    chown -R aipm:aipm /app

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=aipm:aipm . .

# Create startup script
RUN cat > /app/entrypoint.sh << 'EOF'
#!/bin/bash
set -e

echo "🎯 Starting AI Project Manager Production Server"
echo "================================================"

# Wait for database to be ready
echo "⏳ Waiting for database..."
while ! pg_isready -h ${DATABASE_HOST:-localhost} -p ${DATABASE_PORT:-5432} -U ${DATABASE_USER:-aipm_user}; do
    sleep 2
done
echo "✅ Database is ready"

# Run database migrations if needed
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "📊 Running database migrations..."
    python database_migrations.py || echo "⚠️  Migration failed or already completed"
fi

# Start the application
echo "🚀 Starting production server..."
exec gunicorn \
    --bind 0.0.0.0:${PORT:-5001} \
    --workers ${GUNICORN_WORKERS} \
    --threads ${GUNICORN_THREADS} \
    --timeout ${GUNICORN_TIMEOUT} \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-logfile /app/logs/access.log \
    --error-logfile /app/logs/error.log \
    --log-level info \
    --preload \
    api:app
EOF

RUN chmod +x /app/entrypoint.sh

# Create health check script
RUN cat > /app/healthcheck.sh << 'EOF'
#!/bin/bash
curl -f http://localhost:${PORT:-5001}/api/health || exit 1
EOF

RUN chmod +x /app/healthcheck.sh

# Switch to non-root user
USER aipm

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD /app/healthcheck.sh

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]