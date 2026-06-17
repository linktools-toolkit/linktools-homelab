ARG PREINSTALLED_BASE=/opt/preinstalled
ENV PREINSTALLED_PATH="${PREINSTALLED_BASE}/bin:${PREINSTALLED_BASE}/.local/bin:${PREINSTALLED_BASE}/npm/bin"
ENV PATH="${PATH}:${PREINSTALLED_PATH}"
RUN mkdir -p "${PREINSTALLED_BASE}/bin" "${PREINSTALLED_BASE}/npm"

RUN export HOME="${PREINSTALLED_BASE}" && \
    npm install -g --prefix "${PREINSTALLED_BASE}/npm" --omit=dev \
        @openai/codex@latest \
        @google/gemini-cli@latest && \
    npm cache clean --force && \
    rm -rf "${HOME}/.npm"

RUN export HOME="${PREINSTALLED_BASE}" && \
    export PATH="${HOME}/.local/bin:${PATH}" && \
    curl -fsSL https://claude.ai/install.sh | bash; \
    rm -rf "${HOME}/.cache/claude" "${HOME}/.claude" "${HOME}/.claude.json"
