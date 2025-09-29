FROM ubuntu:22.04

# Install deps for pixi + python
RUN apt-get update && apt-get install -y \
    curl bash python3 python3-pip git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install pixi
RUN curl -fsSL https://pixi.sh/install.sh | bash -s -- --yes \
    && mv ~/.pixi/bin/pixi /usr/local/bin/pixi

