FROM codercom/code-server:{{ VSCODE_TAG }}

USER root
RUN apt-get update && \
    apt-get install -y python3-pip python3-venv nodejs npm && \
    rm -rf /var/lib/apt/lists/*

RUN npm install -g @anthropic-ai/claude-code @openai/codex @google/gemini-cli

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

ARG LT_USER="{{ DOCKER_USER }}"
ARG LT_USER_UID="{{ DOCKER_UID }}"
ARG LT_USER_GID="{{ DOCKER_GID }}"
ARG LT_USER_DIR=/workspace
{% include "Dockerfile_ADD_SUDO_USER" %}
{% include "Dockerfile_USER" %}

ENV PATH=/workspace/.local/bin:$PATH
WORKDIR /workspace
