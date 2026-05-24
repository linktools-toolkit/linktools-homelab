ARG VSCODE_TAG
FROM ghcr.io/coder/code-server:$VSCODE_TAG

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-pip python3-venv nodejs npm bubblewrap socat \
    && rm -rf /var/lib/apt/lists/*

# INCLUDE install-ai-cli.dockerfile
# INCLUDE install-chrome.dockerfile
# INCLUDE setup-preinstalled.dockerfile
# INCLUDE install-ai-agents.dockerfile

RUN printf '%s\n' \
    "export PATH=\$PATH:${PREINSTALLED_PATH}" \
    | tee /etc/profile.d/preinstalled.sh > /dev/null \
    && chmod 644 /etc/profile.d/preinstalled.sh
RUN npm install -g puppeteer && \
    npm cache clean --force

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

USER 1000
