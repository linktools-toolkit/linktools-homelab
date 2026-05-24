ARG PREINSTALLED_BASE=/opt/preinstalled
ENV PREINSTALLED_PATH="${PREINSTALLED_BASE}/bin:${PREINSTALLED_BASE}/npm/bin"
ENV PATH="${PATH}:${PREINSTALLED_PATH}"
RUN mkdir -p "${PREINSTALLED_BASE}/bin" "${PREINSTALLED_BASE}/npm"

RUN npm install -g --prefix "${PREINSTALLED_BASE}/npm" --omit=dev \
        @openai/codex@latest \
        @google/gemini-cli@latest && \
    npm cache clean --force

RUN if command -v curl >/dev/null 2>&1; then \
        curl -fsSL https://claude.ai/install.sh | bash; \
    else \
        wget -qO- https://claude.ai/install.sh | bash; \
    fi && \
    mv "${HOME}/.local/bin/claude" "${PREINSTALLED_BASE}/bin/claude" && \
    rm -rf "${HOME}/.claude" "${HOME}/.claude.json"
