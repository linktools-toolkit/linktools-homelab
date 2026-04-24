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
RUN apt-get update \
    && apt-get install -y git curl python3 sudo wget

RUN mkdir -p -m 755 /etc/apt/keyrings \
	&& out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg \
	&& cat $out | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
	&& chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
	&& mkdir -p -m 755 /etc/apt/sources.list.d \
	&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
	&& apt update \
	&& apt install gh -y

RUN rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy built files and server from build stage
COPY --from=build /app/dist ./dist
COPY --from=build /app/dist-server ./dist-server
COPY --from=build /app/scripts ./scripts
COPY --from=build /app/package*.json ./
COPY --from=build /app/node_modules ./node_modules

ARG LT_USER={{ DOCKER_USER }}
ARG LT_USER_UID={{ DOCKER_UID }}
ARG LT_USER_GID={{ DOCKER_GID }}
ARG LT_USER_DIR=/workspace
{% include "Dockerfile_ADD_SUDO_USER" %}
{% include "Dockerfile_USER" %}

ENV NPM_CONFIG_PREFIX=/workspace/.node_modules
ENV NPM_CONFIG_REGISTRY={{ CODER_NPM_REGISTRY }}
RUN mkdir -p /workspace/.node_modules

ENV PATH=/workspace/.local/bin:/workspace/.node_modules/bin:$PATH
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
        'import { initializeDatabase, userDb } from "/app/dist-server/server/database/db.js";' \
        'await initializeDatabase();' \
        'if (!userDb.hasUsers()) {' \
        '  userDb.createUser("admin", "$2b$12$N2aNoQ0Jv425ocxt.V4SQe2q1EI1/3z8Z8MVcNKOmKJjTkVqdlY9u");' \
        '  console.log("Created platform user: admin");' \
        '}' \
        > /tmp/init-user.mjs \
      && node /tmp/init-user.mjs; \
    fi

CMD ["node", "/app/dist-server/server/index.js"]
