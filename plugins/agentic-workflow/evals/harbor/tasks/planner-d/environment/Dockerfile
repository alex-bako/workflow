# Build inputs bundle/ and workspace/ come from ../../../prepare.py.
FROM node:22-bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git python3 ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/

COPY bundle/ /opt/aw/
COPY workspace/ /app/
WORKDIR /app
RUN git init -q -b main \
    && git add -A \
    && git -c user.name=dev -c user.email=dev@example.com commit -q -m "base"
