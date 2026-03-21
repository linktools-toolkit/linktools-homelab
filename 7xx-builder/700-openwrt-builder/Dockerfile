FROM ubuntu:24.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update -y \
    && apt-get install -y -y ack antlr3 asciidoc autoconf automake autopoint binutils bison build-essential \
        bzip2 ccache clang cmake cpio curl device-tree-compiler flex gawk gcc-multilib g++-multilib gettext \
        genisoimage git gperf haveged help2man intltool libc6-dev-i386 libelf-dev libfuse-dev libglib2.0-dev \
        libgmp3-dev libltdl-dev libmpc-dev libmpfr-dev libncurses5-dev libncursesw5-dev libpython3-dev \
        libreadline-dev libssl-dev libtool llvm lrzsz libnsl-dev ninja-build p7zip p7zip-full patch pkgconf \
        python3 python3-pyelftools python3-setuptools qemu-utils rsync scons squashfs-tools subversion \
        swig texinfo uglifyjs upx-ucl unzip vim wget xmlto xxd zlib1g-dev

ARG ARG_USER={{ DOCKER_USER }}
ARG ARG_USER_UID={{ DOCKER_UID }}
ARG ARG_USER_GID={{ DOCKER_GID }}
ARG ARG_USER_DIR=/workspace
{% include "Dockerfile_ADD_SUDO_USER" %}
{% include "Dockerfile_USER" %}

ARG ARG_GIT_NAME={{ CODER_GIT_NAME }}
ARG ARG_GIT_EMAIL={{ CODER_GIT_EMAIL }}
ARG ARG_GIT_HTTP_SSLVERIFY=false
{% include "Dockerfile_GIT_CONFIG" %}

CMD ["tail", "-f", "/dev/null"]
