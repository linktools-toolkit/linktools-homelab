FROM node:22-bookworm-slim

ARG MCP_PLAYWRIGHT_VERSION=0.0.83
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
WORKDIR /opt/playwright

# Install the Chromium revision required by the selected MCP version.
RUN npm install --save-exact "@playwright/mcp@${MCP_PLAYWRIGHT_VERSION}" \
    && ./node_modules/.bin/playwright install --with-deps --no-shell chromium \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        xvfb x11-utils x11vnc openbox novnc websockify curl fonts-noto-cjk tini \
    && ln -sf vnc.html /usr/share/novnc/index.html \
    && chmod -R a+rX /ms-playwright \
    && mkdir -p /workspace \
    && chown node:node /workspace \
    && rm -rf /var/lib/apt/lists/* /root/.npm

COPY .github/docker/mcp-playwright/entrypoint.sh /usr/local/bin/mcp-playwright-entrypoint.sh

ENV HOME=/workspace DISPLAY=:99
WORKDIR /workspace
USER node
EXPOSE 6080 8931
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS http://127.0.0.1:6080/vnc.html >/dev/null \
        && curl -fsS http://127.0.0.1:9222/json/version >/dev/null \
        && curl -sS http://127.0.0.1:8931/mcp >/dev/null
ENTRYPOINT ["/usr/bin/tini", "--", "/bin/bash", "/usr/local/bin/mcp-playwright-entrypoint.sh"]
