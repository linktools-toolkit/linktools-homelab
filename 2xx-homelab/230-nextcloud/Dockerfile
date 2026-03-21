FROM nextcloud:{{ NEXTCLOUD_TAG }}

# RUN apt-get update && \
#     apt-get install -y ffmpeg python3 curl aria2 youtube-dl && \
#     ln -sf /usr/bin/aria2c /usr/local/bin/aria2c && \
#     ln -sf /usr/bin/youtube-dl /usr/local/bin/youtube-dl \
#     rm -rf /var/lib/apt/lists/*

COPY overlay/scripts /scripts
COPY overlay/docker-entrypoint-hooks.d/before-starting/* /docker-entrypoint-hooks.d/before-starting
COPY overlay/docker-entrypoint-hooks.d/post-installation/* /docker-entrypoint-hooks.d/post-installation
COPY overlay/docker-entrypoint-hooks.d/post-upgrade/* /docker-entrypoint-hooks.d/post-upgrade

RUN mkdir -p /usr/local/etc/php/conf.d/ && \
    chmod 777 /usr/local/etc/php/conf.d/

ARG ARG_USER="{{ DOCKER_USER }}"
ARG ARG_USER_UID="{{ DOCKER_UID }}"
ARG ARG_USER_GID="{{ DOCKER_GID }}"
{% include "Dockerfile_ADD_USER" %}
