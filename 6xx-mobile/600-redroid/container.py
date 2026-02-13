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
from linktools.core import Config
from linktools.decorator import cached_property
from linktools.rich import confirm


class Container(BaseContainer):

    @cached_property
    def configs(self):
        return dict(
            REDROID_IMAGE="iceblacktea/redroid-arm64:12.0.0-241218",
            REDROID_COUNT=Config.Prompt(default=3, type=int, cached=True),
            REDROID_WIDTH=Config.Alias(default=720, type=int),
            REDROID_HEIGHT=Config.Alias(default=1280, type=int),
            REDROID_DPI=Config.Alias(default=320, type=int),
            REDROID_ADB_PORT=Config.Prompt(default=5555, type=int, cached=True),
            REDROID_GPU_MODE=Config.Prompt(default="mali", type=str, choices=["auto", "host", "guest", "mali"], cached=True),
            REDROID_RADIO=Config.Confirm(default=True, cached=True),
            REDROID_WIFI=Config.Confirm(default=True, cached=True),
            REDROID_WIFI_GATEWAY="10.23.45.1/24",
            REDROID_MAGISK=Config.Confirm(default=True, cached=True),
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
        if confirm(f"Clean {name} data files", default=False) is False:
            self.logger.warning(f"Cancel clean {path}")
            return -1
        shutil.rmtree(path, ignore_errors=True)
