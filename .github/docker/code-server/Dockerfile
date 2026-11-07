ARG VSCODE_TAG

FROM golang:bookworm AS golang

FROM ghcr.io/coder/code-server:$VSCODE_TAG

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Expose code-server's bundled Node for npm and the shared tools.
RUN ln -sf /usr/lib/code-server/lib/node /usr/local/bin/node \
    && ln -sf node /usr/local/bin/nodejs \
    && node -e "if (parseInt(process.versions.node, 10) < 22) throw new Error('Node.js 22+ is required')"

# INCLUDE install-base-cli.dockerfile
# INCLUDE install-chrome.dockerfile
# INCLUDE install-preinstalled.dockerfile

COPY --from=golang /usr/local/go "${PREINSTALLED_BASE}/go"
RUN ln -s "${PREINSTALLED_BASE}/go/bin/go" "${PREINSTALLED_BASE}/bin/go"

RUN printf '%s\n' \
    'export UV_INSTALL_DIR='"${PREINSTALLED_BASE}/bin" \
    'export UV_PYTHON_INSTALL_DIR='"${PREINSTALLED_BASE}/python" \
    'export UV_PYTHON_BIN_DIR='"${PREINSTALLED_BASE}/bin" \
    >> "${PREINSTALLED_BASE}/.env" && \
    . "${PREINSTALLED_BASE}/.env" && \
    curl -fsSL https://astral.sh/uv/install.sh | bash && \
    uv python install 3.13 --default

ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome \
    PUPPETEER_SKIP_DOWNLOAD=true

RUN . "${PREINSTALLED_BASE}/.env" \
    && npm install -g --omit=dev puppeteer \
    && npm --cache="${PREINSTALLED_BASE}/.npm" cache clean --force \
    && rm -rf "${PREINSTALLED_BASE}/.npm"

RUN node -e " \
  const fs = require('fs'); \
  const path = '/usr/lib/code-server/lib/vscode/product.json'; \
  const p = JSON.parse(fs.readFileSync(path, 'utf8')); \
  const trusted = p.linkProtectionTrustedDomains || []; \
  if (!trusted.includes('https://marketplace.visualstudio.com')) trusted.push('https://marketplace.visualstudio.com'); \
  p.linkProtectionTrustedDomains = trusted; \
  p.extensionsGallery = { \
    serviceUrl: 'https://marketplace.visualstudio.com/_apis/public/gallery', \
    cacheUrl: 'https://vscode.blob.core.windows.net/gallery/index', \
    itemUrl: 'https://marketplace.visualstudio.com/items', \
    controlUrl: '', \
    recommendationsUrl: '' \
  }; \
  fs.writeFileSync(path, JSON.stringify(p, null, 2)); \
"

RUN printf '%s\n' \
    "export PATH=\$PATH:${PREINSTALLED_PATH}" \
    | tee /etc/profile.d/preinstalled.sh > /dev/null \
    && chmod 644 /etc/profile.d/preinstalled.sh

USER 1000
