ARG VSCODE_TAG
FROM ghcr.io/coder/code-server:$VSCODE_TAG

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-pip python3-venv nodejs npm ripgrep unzip yq bubblewrap socat wget \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p -m 755 /etc/apt/keyrings \
    && out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    && cat $out | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && mkdir -p -m 755 /etc/apt/sources.list.d \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | tee /etc/apt/trusted.gpg.d/google.asc >/dev/null \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable fonts-noto-cjk fonts-wqy-zenhei fonts-wqy-microhei fontconfig \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

ENV PREINSTALLED=/opt/preinstalled
ENV PATH="${PATH}:${PREINSTALLED}/bin:${PREINSTALLED}/npm/bin"
RUN printf '%s\n' \
    'export PREINSTALLED=/opt/preinstalled' \
    'export PATH=$PATH:${PREINSTALLED}/bin:${PREINSTALLED}/npm/bin' \
    | sudo tee /etc/profile.d/preinstalled.sh > /dev/null \
    && sudo chmod 644 /etc/profile.d/preinstalled.sh

RUN mkdir -p "${PREINSTALLED}/npm" \
    && npm install -g --prefix "${PREINSTALLED}/npm" \
        @openai/codex@latest \
        @google/gemini-cli@latest \
        puppeteer \
        npx@latest \
    && npm cache clean --force

RUN curl -fsSL https://claude.ai/install.sh | bash \
    && mkdir -p "${PREINSTALLED}/bin" \
    && mv "${HOME}/.local/bin/claude" "${PREINSTALLED}/bin/claude" \
    && rm -rf "${HOME}/.claude" "${HOME}/.claude.json"

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
