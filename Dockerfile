# Angel-X Trading System - Production Dockerfile
# Multi-stage build for optimized production deployment

# ============================================================================
# Stage 1: Builder - Compile dependencies and prepare application
# ============================================================================
FROM python:3.12-slim as builder

# Set working directory
WORKDIR /build

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================
FROM python:3.12-slim

# Metadata
LABEL maintainer="Angel-X Trading System"
LABEL description="Options trading system with AngelOne integration"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    ENVIRONMENT=production \
    TZ=Asia/Kolkata

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 angelx && \
    mkdir -p /app /app/logs /app/data && \
    chown -R angelx:angelx /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=angelx:angelx src/ /app/src/
COPY --chown=angelx:angelx app/ /app/app/
COPY --chown=angelx:angelx config/ /app/config/
COPY --chown=angelx:angelx infra/ /app/infra/
COPY --chown=angelx:angelx tools/ /app/tools/
COPY --chown=angelx:angelx scripts/ /app/scripts/
COPY --chown=angelx:angelx main.py /app/

# Create config.py from example if not exists
RUN if [ ! -f /app/config/config.py ]; then \
    cp /app/config/config.example.py /app/config/config.py; \
    fi

# Switch to non-root user
USER angelx

# Expose port for API
EXPOSE 5000

# Health check - use /monitor/health endpoint (standardized with app)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command - run the main application
CMD ["python", "main.py"]
