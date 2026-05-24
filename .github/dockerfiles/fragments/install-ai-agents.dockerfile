ARG AI_AGENTS_BASE=/opt/ai-agents
ENV AI_AGENTS_PATH="${AI_AGENTS_BASE}/bin:${AI_AGENTS_BASE}/npm/bin"
ENV PATH="${PATH}:${AI_AGENTS_PATH}"

RUN mkdir -p "${AI_AGENTS_BASE}/bin" "${AI_AGENTS_BASE}/npm"

RUN npm install -g --prefix "${AI_AGENTS_BASE}/npm" --omit=dev \
        @openai/codex@latest \
        @google/gemini-cli@latest && \
    npm cache clean --force

RUN if command -v curl >/dev/null 2>&1; then \
        curl -fsSL https://claude.ai/install.sh | bash; \
    else \
        wget -qO- https://claude.ai/install.sh | bash; \
    fi && \
    mv "${HOME}/.local/bin/claude" "${AI_AGENTS_BASE}/bin/claude" && \
    rm -rf "${HOME}/.claude" "${HOME}/.claude.json"
