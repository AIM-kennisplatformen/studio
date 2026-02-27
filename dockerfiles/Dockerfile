# ==============================
# Base image
# ==============================
FROM ghcr.io/prefix-dev/pixi:latest

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

# System dependencies (torch + sentence-transformers need build tools)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    git \
    curl \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install hatchling to build project
RUN wget -qO- https://pixi.sh/install.sh | sh

# Copy only dependency files first (better layer caching)
COPY pyproject.toml pixi.lock README.md ./

# Install project dependencies
RUN pixi install --frozen

# Copy source code
COPY src ./src

# Default command (overridden by compose)
CMD ["pixi", "run", "python", "-m", "uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "10090"]