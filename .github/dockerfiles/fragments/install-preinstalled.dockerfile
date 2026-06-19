ARG PREINSTALLED_BASE=/opt/preinstalled
ENV PREINSTALLED_PATH="${PREINSTALLED_BASE}/bin:${PREINSTALLED_BASE}/.local/bin:${PREINSTALLED_BASE}/npm/bin"
ENV PATH="${PATH}:${PREINSTALLED_PATH}"
RUN mkdir -p "${PREINSTALLED_BASE}/bin" "${PREINSTALLED_BASE}/npm"

RUN printf '%s\n' \
    'export HOME='"${PREINSTALLED_BASE}" \
    'export PATH='"${PREINSTALLED_PATH}"':$PATH' \
    'export NPM_CONFIG_PREFIX='"${PREINSTALLED_BASE}/npm" \
    > "${PREINSTALLED_BASE}/env.sh"

RUN . "${PREINSTALLED_BASE}/env.sh" && \
    npm install -g --omit=dev \
        @openai/codex@latest \
        @google/gemini-cli@latest && \
    npm cache clean --force && \
    rm -rf "${HOME}/.npm"

RUN . "${PREINSTALLED_BASE}/env.sh" && \
    curl -fsSL https://claude.ai/install.sh | bash && \
    rm -rf "${HOME}/.cache/claude" "${HOME}/.claude" "${HOME}/.claude.json"
