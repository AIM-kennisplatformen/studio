FROM ubuntu:22.04

# Install deps for pixi + python
RUN apt-get update && apt-get install -y \
    curl bash python3 python3-pip git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install pixi
RUN curl -fsSL https://pixi.sh/install.sh | bash -s -- --yes \
    && mv ~/.pixi/bin/pixi /usr/local/bin/pixi


# ==========================================================
# 2. Copy Pixi project files
# ==========================================================
COPY pyproject.toml .
COPY pixi.lock .
COPY .pixi/ .pixi/

# Install environment (no dev deps unless needed)
RUN pixi install --locked

# ==========================================================
# 3. Copy backend code + static files
# ==========================================================
COPY src/backend ./src/backend
COPY kg ./kg    

# ==========================================================
# 4. Expose port + run FastAPI
# ==========================================================
ENV PORT=9000

EXPOSE 9000

CMD ["pixi", "run", "python", "-m", "uvicorn", "src.backend.endpoints:app", "--host", "0.0.0.0", "--port", "9000"]
