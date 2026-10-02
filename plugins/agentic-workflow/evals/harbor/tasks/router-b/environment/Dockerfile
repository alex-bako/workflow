# Build inputs bundle/ and workspace/ come from ../../../prepare.py.
FROM node:22-bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git python3 ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/

# Logging stubs first on PATH: gh is not installed and every call is recorded;
# git calls are recorded, then run.
RUN printf '#!/bin/sh\necho "$*" >> /var/log/gh-calls.log\nexit 1\n' > /usr/local/bin/gh \
    && printf '#!/bin/sh\necho "$*" >> /var/log/git-calls.log\nexec /usr/bin/git "$@"\n' > /usr/local/bin/git \
    && chmod +x /usr/local/bin/gh /usr/local/bin/git

COPY bundle/ /opt/aw/
COPY workspace/base/ /app/
COPY workspace/head.patch /tmp/head.patch
WORKDIR /app
# Fixed dates keep the base and head SHAs identical across builds.
RUN export GIT_AUTHOR_DATE=2026-01-05T10:00:00Z GIT_COMMITTER_DATE=2026-01-05T10:00:00Z \
    && g() { /usr/bin/git -c user.name=dev -c user.email=dev@example.com "$@"; } \
    && g init -q -b main && g add -A && g commit -q -m "base" && g tag base \
    && g apply --index /tmp/head.patch \
    && export GIT_AUTHOR_DATE=2026-01-06T10:00:00Z GIT_COMMITTER_DATE=2026-01-06T10:00:00Z \
    && g commit -q -m "T1: prices in integer cents" \
    && rm /tmp/head.patch
