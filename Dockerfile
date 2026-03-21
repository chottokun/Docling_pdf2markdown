# --- Build Stage (Optional but kept simple with BuildKit) ---
FROM python:3.11-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app/src:${PYTHONPATH}" \
    DOCLING_UPLOAD_DIR="/app/data/uploads" \
    DOCLING_OUTPUT_DIR="/app/data/output" \
    HF_HOME="/app/data/models" \
    UV_COMPILE_BYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# Install system dependencies and tini
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    libxcb1 \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    tini && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid 1001 -m -s /bin/bash appuser

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Create persistent directories with correct ownership
RUN mkdir -p /app/data/uploads /app/data/output /app/data/models \
    /usr/local/lib/python3.11/site-packages/rapidocr/models && \
    chown -R appuser:appuser /app

# Install dependencies separately to maximize layer caching.
# Using BuildKit cache mount for uv to speed up re-builds.
COPY pyproject.toml /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    mkdir -p /app/src/docling_lib && \
    touch /app/src/docling_lib/__init__.py && \
    uv pip install .

# Copy source code and tests
COPY ./src /app/src
COPY ./tests /app/tests

# Final ownership adjustment
RUN chown -R appuser:appuser /app

# Use tini as the entrypoint to handle signals correctly
ENTRYPOINT ["/usr/bin/tini", "--"]

# Default to running the server
USER appuser
EXPOSE 8000

# Healthcheck to monitor app status (using GET instead of HEAD/spider)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 -O- http://localhost:8000/ || exit 1

CMD ["uvicorn", "docling_lib.server:app", "--host", "0.0.0.0", "--port", "8000"]
