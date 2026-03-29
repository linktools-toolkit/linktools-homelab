FROM codercom/code-server:{{ VSCODE_TAG }}

USER root
RUN apt-get update && \
    apt-get install -y python3-pip python3-venv nodejs npm && \
    rm -rf /var/lib/apt/lists/*

RUN npm install -g @anthropic-ai/claude-code @openai/codex @google/gemini-cli

ARG LT_USER="{{ DOCKER_USER }}"
ARG LT_USER_UID="{{ DOCKER_UID }}"
ARG LT_USER_GID="{{ DOCKER_GID }}"
ARG LT_USER_DIR=/workspace
{% include "Dockerfile_ADD_SUDO_USER" %}
{% include "Dockerfile_USER" %}

ENV PATH=/workspace/.local/bin:$PATH
WORKDIR /workspace
