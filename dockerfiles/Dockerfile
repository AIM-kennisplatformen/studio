# ==============================
# Base image
# ==============================
FROM ghcr.io/prefix-dev/pixi:latest

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

COPY pyproject.toml pixi.lock ./

RUN pixi install --frozen

COPY src ./src

RUN pixi run npm install --prefix src/frontend \
    && VITE_BACKEND_BASE_URL="${BACKEND_BASE_URL:-http://localhost:10090}" pixi run npm run build --prefix src/frontend

# Remove any cache of pixi (which is useless anyways)
RUN rm -r /root/.cache/*

EXPOSE 10090

# Default command (overridden by compose)
CMD ["pixi", "run", "python", "-m", "uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "10090", "--reload", "--reload-dir", "src/backend"]
