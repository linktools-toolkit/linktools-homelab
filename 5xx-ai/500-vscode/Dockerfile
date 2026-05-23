FROM ghcr.io/linktools-toolkit/code-server:{{ VSCODE_TAG }}

USER root

ARG LT_USER="{{ DOCKER_USER }}"
ARG LT_USER_UID="{{ DOCKER_UID }}"
ARG LT_USER_GID="{{ DOCKER_GID }}"
ARG LT_USER_DIR=/workspace
{% include "Dockerfile_ADD_SUDO_USER" %}
{% include "Dockerfile_USER" %}

RUN mkdir -p /workspace/.node_modules

ENV NPM_CONFIG_PREFIX=/workspace/.node_modules
ENV NPM_CONFIG_REGISTRY={{ CODER_NPM_REGISTRY }}
ENV PATH=/workspace/.local/bin:/workspace/.node_modules/bin:$PATH
RUN printf '%s\n' \
    'export NPM_CONFIG_PREFIX=/workspace/.node_modules' \
    'export NPM_CONFIG_REGISTRY={{ CODER_NPM_REGISTRY }}' \
    'export PATH=/workspace/.local/bin:/workspace/.node_modules/bin:$PATH' \
    | sudo tee /etc/profile.d/workspace-env.sh > /dev/null

WORKDIR /workspace
