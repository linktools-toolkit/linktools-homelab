FROM codercom/code-server:{{ VSCODE_TAG }}

USER root
RUN apt-get update && \
    apt-get install -y python3-pip python3-venv nodejs npm && \
    rm -rf /var/lib/apt/lists/*

RUN npm install -g @anthropic-ai/claude-code @openai/codex @google/gemini-cli

ENV HOME=/workspace
ENV PATH=/workspace/.local/bin:$PATH
ENV USER={{ DOCKER_USER }}

ARG USER_DIR=/workspace
{% include "Dockerfile_ADD_SUDO_USER" %}
{% include "Dockerfile_USER" %}

RUN sudo mkdir -p /workspace/.claude /workspace/.cloudcli /workspace/.cursor /workspace/.gemini /workspace/projects
RUN sudo chown -R {{ DOCKER_UID }}:{{ DOCKER_GID }} /workspace

WORKDIR /workspace
