FROM ghcr.io/linktools-toolkit/aionui:{{ AIONUI_TAG }}

USER root

RUN apt-get update \
    && apt-get install -y ripgrep unzip wget curl yq nodejs npm

RUN mkdir -p -m 755 /etc/apt/keyrings \
    && out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    && cat $out | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && mkdir -p -m 755 /etc/apt/sources.list.d \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

ARG LT_USER="{{ DOCKER_USER }}"
ARG LT_USER_UID="{{ DOCKER_UID }}"
ARG LT_USER_GID="{{ DOCKER_GID }}"
ARG LT_USER_DIR=/workspace
{% include "Dockerfile_ADD_SUDO_USER" %}
{% include "Dockerfile_USER" %}

RUN mkdir -p /workspace/.node_modules

ENV HOME=/workspace
ENV NPM_CONFIG_PREFIX=/workspace/.node_modules
ENV NPM_CONFIG_REGISTRY={{ CODER_NPM_REGISTRY }}
ENV PATH=/workspace/.local/bin:/workspace/.node_modules/bin:$PATH

WORKDIR /workspace

CMD ["bash", "-c", "cd /app && bun dist-server/server.mjs"]
