FROM ubuntu:24.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update -y \
    && apt full-upgrade -y \
    && apt-get install -y -y ack antlr3 asciidoc autoconf automake autopoint binutils bison build-essential \
        bzip2 ccache clang cmake cpio curl device-tree-compiler flex gawk gcc-multilib g++-multilib gettext \
        genisoimage git gperf haveged help2man intltool libc6-dev-i386 libelf-dev libfuse-dev libglib2.0-dev \
        libgmp3-dev libltdl-dev libmpc-dev libmpfr-dev libncurses5-dev libncursesw5-dev libpython3-dev \
        libreadline-dev libssl-dev libtool llvm lrzsz libnsl-dev ninja-build p7zip p7zip-full patch pkgconf \
        python3 python3-pyelftools python3-setuptools qemu-utils rsync scons squashfs-tools subversion \
        swig texinfo uglifyjs upx-ucl unzip vim wget xmlto xxd zlib1g-dev

# {% if DOCKER_UID != 0 %}

ARG USERNAME={{ DOCKER_USER }}
ARG USER_UID={{ DOCKER_UID }}
ARG USER_GID={{ DOCKER_GID }}

RUN set -eux; \
    if getent group ${USER_GID} >/dev/null; then \
        GROUP_NAME=$(getent group ${USER_GID} | cut -d: -f1); \
    else \
        groupadd -g ${USER_GID} ${USERNAME}; \
        GROUP_NAME=${USERNAME}; \
    fi; \
    \
    if getent passwd ${USER_UID} >/dev/null; then \
        EXISTING_USER=$(getent passwd ${USER_UID} | cut -d: -f1); \
        usermod -l ${USERNAME} ${EXISTING_USER}; \
        usermod -d /home/${USERNAME} -m ${USERNAME}; \
    else \
        useradd -m -u ${USER_UID} -g ${USER_GID} -s /bin/bash ${USERNAME}; \
    fi

ENV HOME=/home/${USERNAME} \
    USER=${USERNAME}

# {% else %}

ENV HOME=/root

# {% endif %}

CMD ["tail", "-f", "/dev/null"]
