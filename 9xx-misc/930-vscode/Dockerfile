FROM codercom/code-server:{{ VSCODE_TAG }}

USER root
RUN apt-get update && \
    apt-get install -y python3-pip python3-venv && \
    rm -rf /var/lib/apt/lists/*

ENV PATH=/home/coder/.local/bin:$PATH

USER {{ DOCKER_UID }}
ENV USER=coder

WORKDIR /home/coder/project
