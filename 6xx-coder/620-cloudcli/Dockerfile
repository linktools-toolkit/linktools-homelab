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

ARG VITE_IS_PLATFORM
ENV VITE_IS_PLATFORM=$VITE_IS_PLATFORM

# Build the frontend
RUN npm run build

# Remove devDependencies after build
RUN npm prune --omit=dev

# Production stage
FROM node:22-slim

# Install runtime dependencies
# Claude Code CLI requires git and other tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    python3 \
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

RUN npm install -g task-master-ai react react-dom
RUN npm install -g @anthropic-ai/claude-code @openai/codex @google/gemini-cli
# RUN curl https://cursor.com/install -fsSL | bash

ARG LT_USER={{ DOCKER_USER }}
ARG LT_USER_UID={{ DOCKER_UID }}
ARG LT_USER_GID={{ DOCKER_GID }}
ARG LT_USER_DIR=/workspace
{% include "Dockerfile_ADD_SUDO_USER" %}
{% include "Dockerfile_USER" %}

WORKDIR /workspace
ENV HOST 0.0.0.0
ENV PORT 3001
EXPOSE 3001
ENV DATABASE_PATH=/workspace/.cloudcli/auth/cloudcli.db
ENV GEMINI_PATH=/workspace/.gemini

ARG VITE_IS_PLATFORM
ENV VITE_IS_PLATFORM=$VITE_IS_PLATFORM

# Init platform user via db.js (runs after build so ESM + bcrypt are available)
# Default credentials: admin / platform
RUN if [ "$VITE_IS_PLATFORM" = "true" ]; then \
      printf '%s\n' \
        'import { initializeDatabase, userDb } from "/app/server/database/db.js";' \
        'await initializeDatabase();' \
        'if (!userDb.hasUsers()) {' \
        '  userDb.createUser("admin", "$2b$12$N2aNoQ0Jv425ocxt.V4SQe2q1EI1/3z8Z8MVcNKOmKJjTkVqdlY9u");' \
        '  console.log("Created platform user: admin");' \
        '}' \
        > /tmp/init-user.mjs \
      && node /tmp/init-user.mjs; \
    fi

CMD ["/app/server/index.js"]
