FROM node:22-bookworm-slim

WORKDIR /app
COPY .github/docker/mcp-push/package*.json ./
RUN npm ci --omit=dev --ignore-scripts \
    && npm cache clean --force
COPY .github/docker/mcp-push/server.mjs ./server.mjs

ENV NODE_ENV=production PORT=8931
USER node
EXPOSE 8931
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD node -e "fetch('http://127.0.0.1:8931/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
CMD ["node", "server.mjs"]
