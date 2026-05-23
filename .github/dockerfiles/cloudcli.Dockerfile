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

ENV HOST=0.0.0.0
ENV PORT=3001
EXPOSE 3001

ARG VITE_IS_PLATFORM=true
ENV VITE_IS_PLATFORM=$VITE_IS_PLATFORM

# Pre-create default admin account (credentials: admin / platform)
RUN printf '%s\n' \
    'if (process.env.VITE_IS_PLATFORM !== "true") { console.log("[init] skipping user init (not platform mode)"); process.exit(0); }' \
    'import { initializeDatabase } from "/app/dist-server/server/modules/database/init-db.js";' \
    'import { userDb } from "/app/dist-server/server/modules/database/repositories/users.js";' \
    'await initializeDatabase();' \
    'if (!userDb.hasUsers()) {' \
    '  userDb.createUser("admin", "$2b$12$N2aNoQ0Jv425ocxt.V4SQe2q1EI1/3z8Z8MVcNKOmKJjTkVqdlY9u");' \
    '  console.log("[init] created default admin user");' \
    '} else {' \
    '  console.log("[init] users already exist, skipping");' \
    '}' \
    > /etc/cloudcli/init_user.mjs

CMD ["sh", "-c", "node /etc/cloudcli/init_user.mjs && node /app/dist-server/server/index.js"]
