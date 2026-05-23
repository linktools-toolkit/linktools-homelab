FROM nousresearch/hermes-agent:{{ HERMES_AGENT_TAG }}

RUN apt-get update && apt-get install -y \
    chromium \
    ca-certificates \
    fontconfig \
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxss1 \
    xdg-utils \
 && fc-cache -fv \
 && rm -rf /var/lib/apt/lists/*

ENV AGENT_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8