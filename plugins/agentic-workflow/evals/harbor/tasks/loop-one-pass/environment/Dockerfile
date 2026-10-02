# Build inputs bundle/, tools/ and workspace/ come from ../../../prepare.py.
FROM node:22-bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git python3 ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/

COPY bundle/ /opt/aw/
# Tracker backend: tools/gh records the calling command, then runs tools/fake-gh on
# state.json. direct-gh goes first on PATH as `gh`: it logs and refuses any direct call.
COPY tools/ /opt/tools/
RUN mv /opt/tools/direct-gh /usr/local/bin/gh \
    && chmod 755 /usr/local/bin/gh /opt/tools/gh /opt/tools/fake-gh \
    && chmod 777 /opt/tools && chmod 666 /opt/tools/state.json \
    && touch /var/log/gh-direct.log /var/log/tracker-calls.log \
    && chmod 666 /var/log/gh-direct.log /var/log/tracker-calls.log
ENV AW_TRACKER_GH=/opt/tools/gh AW_FAKE_GH_STATE=/opt/tools/state.json

# Project committed on main, no remote. The role profiles are registered as project
# subagents (git-excluded, so they never show in the diff).
COPY workspace/base/ /app/
WORKDIR /app
RUN git config --global user.name dev \
    && git config --global user.email dev@example.com \
    && git init -q -b main && git add -A && git commit -q -m "base" \
    && mkdir .claude && cp -r /opt/aw/agents .claude/agents \
    && echo ".claude/" >> .git/info/exclude
