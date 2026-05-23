FROM ghcr.io/linktools-toolkit/cloudcli:{{ CLOUD_CLI_TAG }}

USER root

ARG LT_USER="{{ DOCKER_USER }}"
ARG LT_USER_UID="{{ DOCKER_UID }}"
ARG LT_USER_GID="{{ DOCKER_GID }}"
ARG LT_USER_DIR=/workspace

RUN mkdir -p /opt/cloudcli \
    && cp /etc/cloudcli/auth/default.db /opt/cloudcli/default.db \
    && chown -R ${LT_USER_UID}:${LT_USER_GID} /opt/cloudcli

{% include "Dockerfile_ADD_SUDO_USER" %}
{% include "Dockerfile_USER" %}

RUN mkdir -p /workspace/.node_modules

ENV NPM_CONFIG_PREFIX=/workspace/.node_modules
ENV NPM_CONFIG_REGISTRY={{ CODER_NPM_REGISTRY }}
ENV PATH=/workspace/.local/bin:/workspace/.node_modules/bin:$PATH
ENV DATABASE_PATH=/opt/cloudcli/default.db

WORKDIR /workspace
