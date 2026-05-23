# Build stage
FROM node:22-slim AS build

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    make \
    g++ \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ARG CLOUDCLI_REF=main
RUN git init . \
    && git remote add origin https://github.com/siteboon/claudecodeui.git \
    && git fetch --depth 1 origin $CLOUDCLI_REF \
    && git checkout FETCH_HEAD

RUN npm install && npm cache clean --force

ARG VITE_IS_PLATFORM=true
ENV VITE_IS_PLATFORM=$VITE_IS_PLATFORM

RUN npm run build
RUN npm prune --omit=dev

# Production stage
FROM node:22-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl python3 sudo wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p -m 755 /etc/apt/keyrings /etc/apt/sources.list.d \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/dist-server ./dist-server
COPY --from=build /app/scripts ./scripts
COPY --from=build /app/package*.json ./
COPY --from=build /app/node_modules ./node_modules

ENV PREINSTALLED=/opt/preinstalled
ENV PATH="${PATH}:${PREINSTALLED}/bin:${PREINSTALLED}/npm/bin"

RUN mkdir -p "${PREINSTALLED}/npm" \
    && npm install -g --prefix "${PREINSTALLED}/npm" \
        @openai/codex@latest \
        @google/gemini-cli@latest \
        npx@latest \
    && npm cache clean --force

RUN curl -fsSL https://claude.ai/install.sh | bash \
    && mkdir -p "${PREINSTALLED}/bin" \
    && mv "${HOME}/.local/bin/claude" "${PREINSTALLED}/bin/claude" \
    && rm -rf "${HOME}/.claude" "${HOME}/.claude.json"

ARG VITE_IS_PLATFORM=true
ENV VITE_IS_PLATFORM=$VITE_IS_PLATFORM

ENV HOST=0.0.0.0
ENV PORT=3001
EXPOSE 3001
ENV DATABASE_PATH=/var/lib/cloudcli/auth/cloudcli.db

# Pre-create default admin account (credentials: admin / platform)
RUN mkdir -p /var/lib/cloudcli/auth && chmod 777 /var/lib/cloudcli/auth && \
    if [ "$VITE_IS_PLATFORM" = "true" ]; then \
      printf '%s\n' \
          'import { initializeDatabase } from "/app/dist-server/server/modules/database/init-db.js";' \
          'import { userDb } from "/app/dist-server/server/modules/database/repositories/users.js";' \
          'await initializeDatabase();' \
          'if (!userDb.hasUsers()) {' \
          '  userDb.createUser("admin", "$2b$12$N2aNoQ0Jv425ocxt.V4SQe2q1EI1/3z8Z8MVcNKOmKJjTkVqdlY9u");' \
          '  console.log("Created platform user: admin");' \
          '}' \
          > /tmp/init-user.mjs \
      && node /tmp/init-user.mjs; \
    fi

CMD ["node", "/app/dist-server/server/index.js"]
