# ==============================
# Base image
# ==============================
FROM ghcr.io/prefix-dev/pixi:latest

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

# Install hatchling to build project
RUN wget -qO- https://pixi.sh/install.sh | sh

# Copy only dependency files first (better layer caching)
COPY pyproject.toml pixi.lock ./

# Install project dependencies
RUN pixi install --frozen

# Copy source code
COPY src ./src

RUN rm -r /root/.cache/*
# Default command (overridden by compose)
CMD ["pixi", "run", "python", "-m", "uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "10090"]