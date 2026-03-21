# Build stage
FROM node:22-slim AS build

# Install build dependencies for node-pty and better-sqlite3
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy package files
COPY package*.json ./

# Copy scripts directory first because npm install triggers postinstall which needs scripts/fix-node-pty.js
COPY scripts/ ./scripts/

# Install dependencies
RUN npm install

# Copy project files
COPY . .

# Build the frontend
RUN npm run build

# Production stage
FROM node:22-slim

# Install runtime dependencies
# Claude Code CLI requires git and other tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    python3 python3-pip python3-venv \
    sudo \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy built files and server from build stage
COPY --from=build /app/dist ./dist
COPY --from=build /app/server ./server
COPY --from=build /app/shared ./shared
COPY --from=build /app/scripts ./scripts
COPY --from=build /app/package*.json ./
COPY --from=build /app/node_modules ./node_modules

ARG ARG_USER={{ DOCKER_USER }}
ARG ARG_USER_UID={{ DOCKER_UID }}
ARG ARG_USER_GID={{ DOCKER_GID }}
ARG ARG_USER_DIR=/workspace
{% include "Dockerfile_ADD_SUDO_USER" %}
{% include "Dockerfile_USER" %}

ARG ARG_GIT_NAME="{{ CODER_GIT_NAME }}"
ARG ARG_GIT_EMAIL="{{ CODER_GIT_EMAIL }}"
{% include "Dockerfile_GIT_CONFIG" %}

WORKDIR /workspace
ENV HOST 0.0.0.0
ENV PORT 3001
EXPOSE 3001
ENV DATABASE_PATH=/app/data/cloudcli.db
ENV GEMINI_PATH=/workspace/.gemini

RUN sudo npm install -g task-master-ai react react-dom
RUN sudo npm install -g @anthropic-ai/claude-code @openai/codex @google/gemini-cli && \
    curl https://cursor.com/install -fsSL | bash

CMD ["/app/server/index.js"]
