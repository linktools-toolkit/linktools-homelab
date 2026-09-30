RUN if command -v curl >/dev/null 2>&1; then \
        fetch() { curl -fsSL "$1"; }; \
    elif command -v wget >/dev/null 2>&1; then \
        fetch() { wget -qO- "$1"; }; \
    else \
        echo "curl or wget is required but neither is installed" >&2; exit 1; \
    fi && \
    fetch https://dl.google.com/linux/linux_signing_key.pub \
        | tee /etc/apt/trusted.gpg.d/google.asc > /dev/null && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
        >> /etc/apt/sources.list.d/google.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        google-chrome-stable \
        fonts-noto-cjk \
        fonts-wqy-zenhei \
        fonts-wqy-microhei \
        fontconfig && \
    fc-cache -fv && \
    rm -rf /var/lib/apt/lists/*
