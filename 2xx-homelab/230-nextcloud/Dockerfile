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

# {% if DOCKER_UID != 0 %}

RUN (groupadd -g {{ DOCKER_GID }} {{ DOCKER_USER }} || true) && \
    useradd -m -u {{ DOCKER_UID }} -g {{ DOCKER_GID }} {{ DOCKER_USER }}

# {% endif %}
