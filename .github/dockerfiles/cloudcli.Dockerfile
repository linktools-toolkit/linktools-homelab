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
    && apt-get install -y --no-install-recommends python3 sudo \
    && rm -rf /var/lib/apt/lists/*

# INCLUDE install-agent-cli.dockerfile
# INCLUDE install-preinstalled.dockerfile

WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/dist-server ./dist-server
COPY --from=build /app/scripts ./scripts
COPY --from=build /app/package*.json ./
COPY --from=build /app/node_modules ./node_modules

ARG VITE_IS_PLATFORM=true

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
