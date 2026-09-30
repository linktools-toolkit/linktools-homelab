#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@author  : Hu Ji
@file    : deploy.py 
@time    : 2023/05/21
@site    :  
@software: PyCharm 

              ,----------------,              ,---------,
         ,-----------------------,          ,"        ,"|
       ,"                      ,"|        ,"        ,"  |
      +-----------------------+  |      ,"        ,"    |
      |  .-----------------.  |  |     +---------+      |
      |  |                 |  |  |     | -==----'|      |
      |  | $ sudo rm -rf / |  |  |     |         |      |
      |  |                 |  |  |/----|`---=    |      |
      |  |                 |  |  |   ,/|==== ooo |      ;
      |  |                 |  |  |  // |(((( [33]|    ,"
      |  `-----------------'  |," .;'| |((((     |  ,"
      +-----------------------+  ;;  | |         |,"
         /_)______________(_/  //'   | +---------+
    ___________________________/___  `,
   /  oooooooooooooooo  .o.  oooo /,   `,"-----------
  / ==ooooooooooooooo==.o.  ooo= //   ,``--{)B     ,"
 /_==__==========__==_ooo__ooo=_/'   /___________,"
"""
import os
import shutil

from linktools.cli import subcommand
from linktools.cntr import BaseContainer
from linktools.core import ConfigField, PromptProvider, ConfirmProvider
from linktools.decorator import cached_property
from linktools.rich import confirm


class Container(BaseContainer):

    @cached_property
    def configs(self):
        return dict(
            REDROID_IMAGE="iceblacktea/redroid-arm64:12.0.0-241218",
            REDROID_COUNT=ConfigField(cast=int, provider=PromptProvider(default=3, cached=True)),
            REDROID_WIDTH=ConfigField(cast=int, default=720),
            REDROID_HEIGHT=ConfigField(cast=int, default=1280),
            REDROID_DPI=ConfigField(cast=int, default=320),
            REDROID_ADB_PORT=ConfigField(cast=int, provider=PromptProvider(default=5555, cached=True)),
            REDROID_GPU_MODE=ConfigField(provider=PromptProvider(
                default="mali", choices=["auto", "host", "guest", "mali"], cached=True,
            )),
            REDROID_RADIO=ConfigField(cast=bool, provider=ConfirmProvider(default=True, cached=True)),
            REDROID_WIFI=ConfigField(cast=bool, provider=ConfirmProvider(default=True, cached=True)),
            REDROID_WIFI_GATEWAY="10.23.45.1/24",
            REDROID_MAGISK=ConfigField(cast=bool, provider=ConfirmProvider(default=True, cached=True)),
        )

    @cached_property
    def overlay_files(self):
        result = dict()
        overlay_path = os.path.abspath(self.get_app_path("overlay"))
        for root, dirs, files in os.walk(overlay_path):
            for name in files:
                path = os.path.abspath(os.path.join(root, name))
                result[path] = os.path.join("/", path[len(overlay_path):])
        return result

    @subcommand("clean", help="Clean redroid data files")
    def on_exec_clean(self):
        service = self.choose_service()
        name = service.get("container_name")
        path = self.get_app_path("data", name)
        if not confirm(f"Clean {name} data files", default=False):
            self.logger.warning(f"Cancel clean {path}")
            return -1
        shutil.rmtree(path, ignore_errors=True)
