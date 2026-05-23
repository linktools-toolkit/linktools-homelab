ARG PREINSTALLED_BASE=/opt/preinstalled
ENV PREINSTALLED_PATH="${PREINSTALLED_BASE}/bin:${PREINSTALLED_BASE}/npm/bin:${PREINSTALLED_BASE}/bun/bin"
ENV PATH="${PATH}:${PREINSTALLED_PATH}"

RUN if command -v curl >/dev/null 2>&1; then \
        fetch() { curl -fsSL "$1"; }; \
    elif command -v wget >/dev/null 2>&1; then \
        fetch() { wget -qO- "$1"; }; \
    else \
        echo "curl or wget is required but neither is installed" >&2; exit 1; \
    fi && \
    mkdir -p "${PREINSTALLED_BASE}/bun/bin" && \
    fetch https://bun.sh/install | BUN_INSTALL="${PREINSTALLED_BASE}/bun" bash && \
    corepack enable && \
    mkdir -p "${PREINSTALLED_BASE}/npm" && \
    npm install -g --prefix "${PREINSTALLED_BASE}/npm" \
        @openai/codex@latest \
        @google/gemini-cli@latest \
        task-master-ai@latest && \
    npm cache clean --force && \
    fetch https://claude.ai/install.sh | bash && \
    mkdir -p "${PREINSTALLED_BASE}/bin" && \
    mv "${HOME}/.local/bin/claude" "${PREINSTALLED_BASE}/bin/claude" && \
    rm -rf "${HOME}/.claude" "${HOME}/.claude.json"
