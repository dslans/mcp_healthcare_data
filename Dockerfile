# Use Python 3.11 slim image for optimal compatibility and size
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies including build tools for FastMCP 2.11.3
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libffi-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Upgrade pip and install wheel for better dependency resolution
RUN pip install --upgrade pip setuptools wheel

# Install dependencies in stages to handle potential conflicts
# First install core build dependencies
RUN pip install --no-cache-dir \
    pydantic==2.11.7 \
    pydantic-core==2.33.2 \
    typing-extensions==4.14.1 \
    cryptography==45.0.6

# Then install FastMCP and its dependencies
RUN pip install --no-cache-dir fastmcp==2.11.3 mcp==1.12.4

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY healthcare_mcp_server.py .

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Port not needed for MCP stdio protocol
# EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import healthcare_mcp_server; print('Health check passed')" || exit 1

# Default command for MCP protocol via stdio
CMD ["python", "healthcare_mcp_server.py"]
