ARG PREINSTALLED_BASE=/opt/preinstalled
ENV PREINSTALLED_PATH="${PREINSTALLED_BASE}/home/.local/bin:${PREINSTALLED_BASE}/npm/bin"
ENV PATH="${PATH}:${PREINSTALLED_PATH}"
RUN mkdir -p "${PREINSTALLED_BASE}/home" "${PREINSTALLED_BASE}/npm"

RUN npm install -g --prefix "${PREINSTALLED_BASE}/npm" --omit=dev \
        @openai/codex@latest \
        @google/gemini-cli@latest && \
    npm cache clean --force

RUN export HOME="${PREINSTALLED_BASE}/home" && \
    export PATH="${HOME}/.local/bin:${PATH}" && \
    mkdir -p "${HOME}" && \
    if command -v curl >/dev/null 2>&1; then \
        curl -fsSL https://claude.ai/install.sh | bash; \
    else \
        wget -qO- https://claude.ai/install.sh | bash; \
    fi

RUN export HOME="${PREINSTALLED_BASE}/home" && \
    export PATH="${HOME}/.local/bin:${PATH}" && \
    mkdir -p "${HOME}" && \
    if command -v curl >/dev/null 2>&1; then \
        curl -fsSL https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.sh | bash; \
    else \
        wget -qO- https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.sh | bash; \
    fi
