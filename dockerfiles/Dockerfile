# ==============================
# Base image
# ==============================
FROM ghcr.io/prefix-dev/pixi:latest

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

RUN wget -qO- https://pixi.sh/install.sh | sh

COPY pyproject.toml pixi.lock ./

RUN pixi install --frozen

COPY src ./src

# Remove any cache of pixi (which is useless anyways)
RUN rm -r /root/.cache/*

# Default command (overridden by compose)
CMD ["pixi", "run", "python", "-m", "uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "10090"]