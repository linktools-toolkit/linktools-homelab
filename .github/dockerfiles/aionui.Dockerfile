FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y ripgrep unzip wget curl yq nodejs npm ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p -m 755 /etc/apt/keyrings \
    && out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    && cat $out | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && mkdir -p -m 755 /etc/apt/sources.list.d \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | tee /etc/apt/trusted.gpg.d/google.asc >/dev/null \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable fonts-noto-cjk fonts-wqy-zenhei fonts-wqy-microhei fontconfig \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

ENV PREINSTALLED=/opt/preinstalled
ENV PATH="${PATH}:${PREINSTALLED}/bin:${PREINSTALLED}/npm/bin"

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

WORKDIR /app
COPY dist/ ./
RUN chmod +x aionui-web

ENV NODE_ENV=production
ENV AIONUI_PORT=3000
ENV AIONUI_HOST=0.0.0.0
ENV AIONUI_ALLOW_REMOTE=true
ENV AIONUI_DATA_DIR=/data

EXPOSE 3000

CMD ["/app/aionui-web"]
