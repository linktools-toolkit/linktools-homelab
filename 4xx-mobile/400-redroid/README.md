# Redroid

## Dependency

1. Install Python3, Git, [Docker](https://docs.docker.com/engine/install/ubuntu/#install-using-the-convenience-script), [Docker Compose](https://docs.docker.com/compose/install/linux/)

```bash
wget -qO- get.docker.com | bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip git docker-compose-plugin
```

2. Install linktools library and add redroid repository

```bash
python3 -m pip install -U "linktools-cntr"
ct-cntr repo add https://github.com/linktools-toolkit/linktools-homelab  # fetch code from remote repository
```

## Run redroid in arm64 Board

```bash
ct-cntr add redroid                                            # add redroid containers
ct-cntr config set \
    REDROID_COUNT=3 \
    REDROID_GPU_MODE=mali \
    REDROID_VIRTUAL_WIFI=true
ct-cntr up                                                     # start redroid containers
```

## Build in x86_64 PC

Build the redroid image for the first time

```bash
ct-cntr add redroid-builder                                    # add redroid-builder container

#####################
# create and start builder
#####################
ct-cntr config set REDROID_BUILD_PATH=~/redroid                # set the path to store source code
ct-cntr config                                                 # check whether the docker configuration is correct
ct-cntr up                                                     # start redroid-builder container

#####################
# fetch code
#####################
ct-cntr exec redroid-builder init-repo -u https://github.com/redroid-rockchip/platform_manifests.git -b redroid-12.0.0
ct-cntr exec redroid-builder sync-repo

#####################
# build redroid
#####################
ct-cntr exec redroid-builder build-rk3588

#####################
# create redroid image
#####################
ct-cntr exec redroid-builder make-image
```

Build the redroid image for the second time
```bash
ct-cntr update
ct-cntr up                                                     # update code from remote repository
ct-cntr exec redroid-builder sync-repo
ct-cntr exec redroid-builder build-rk3588                      # build redroid
ct-cntr exec redroid-builder make-image                        # create redroid image
```

Export the redroid image to rockchip
```bash
docker save redroid | ssh root@10.10.10.12 docker load
```
