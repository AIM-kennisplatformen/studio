# syntax=docker/dockerfile:1

FROM ghcr.io/prefix-dev/pixi:latest AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY pyproject.toml pixi.lock ./
RUN pixi install --frozen

FROM base AS development

COPY src ./src
COPY mcp_tools.json ./mcp_tools.json

EXPOSE 10090
CMD ["pixi", "run", "python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "10090", "--reload", "--reload-dir", "src"]

FROM base AS release

COPY src ./src
COPY mcp_tools.json ./mcp_tools.json

RUN rm -rf /root/.cache/*

EXPOSE 10090
ENTRYPOINT ["pixi", "run", "python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "10090"]
