FROM ghcr.io/linktools-toolkit/multica:{{ MULTICA_CLIENT_TAG }}

USER root

ARG LT_USER="{{ DOCKER_USER }}"
ARG LT_USER_UID="{{ DOCKER_UID }}"
ARG LT_USER_GID="{{ DOCKER_GID }}"
ARG LT_USER_DIR=/workspace
{% include "Dockerfile_ADD_SUDO_USER" %}
{% include "Dockerfile_USER" %}

WORKDIR /workspace
