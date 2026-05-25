ARG PREINSTALLED_BASE=/opt/preinstalled
ENV PREINSTALLED_PATH="${PREINSTALLED_BASE}/home/.local/bin:${PREINSTALLED_BASE}/npm/bin"
ENV PATH="${PATH}:${PREINSTALLED_PATH}"
RUN mkdir -p "${PREINSTALLED_BASE}/home" "${PREINSTALLED_BASE}/npm"

RUN export HOME="${PREINSTALLED_BASE}/home" && \
    npm install -g --prefix "${PREINSTALLED_BASE}/npm" --omit=dev \
        @openai/codex@latest \
        @google/gemini-cli@latest && \
    npm cache clean --force && \
    rm -rf "${HOME}/.npm"

RUN export HOME="${PREINSTALLED_BASE}/home" && \
    export PATH="${HOME}/.local/bin:${PATH}" && \
    if command -v curl >/dev/null 2>&1; then \
        curl -fsSL https://claude.ai/install.sh | bash; \
    else \
        wget -qO- https://claude.ai/install.sh | bash; \
    fi && \
    rm -rf "${HOME}/.cache/claude" "${HOME}/.claude" "${HOME}/.claude.json"

RUN export HOME="${PREINSTALLED_BASE}/home" && \
    export PATH="${HOME}/.local/bin:${PATH}" && \
    if command -v curl >/dev/null 2>&1; then \
        curl -fsSL https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.sh | bash; \
    else \
        wget -qO- https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.sh | bash; \
    fi
