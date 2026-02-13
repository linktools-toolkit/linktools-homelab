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
import os.path
import shutil
import zipfile
from typing import Iterable

import yaml

from linktools import utils
from linktools.cntr import BaseContainer, ExposeLink
from linktools.core import Config
from linktools.decorator import cached_property


class Container(BaseContainer):

    @cached_property
    def configs(self):
        return dict(
            WS_SCRCPY_TAG="v0.8.1",
            WS_SCRCPY_PORT=Config.Alias(default=8000, type=int),
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_container(
                "ws-scrcpy", "cellphone", "ws-scrcpy",
                self.load_port_url("WS_SCRCPY_PORT", https=False)),
        ]

    @cached_property
    def source_path(self):
        tag = self.get_config("WS_SCRCPY_TAG")

        zip_path = self.get_app_path(f"ws-scrcpy-{tag}.zip")
        source_path = str(zip_path) + ".unzip"

        def init_source_code():
            if not os.path.isdir(source_path):
                file = self.manager.environ.get_url_file(
                    f"https://github.com/NetrisTV/ws-scrcpy/archive/refs/tags/{tag}.zip")
                file.save(zip_path.parent, zip_path.name)
                os.makedirs(source_path, exist_ok=True)
                try:
                    with zipfile.ZipFile(zip_path) as f:
                        for names in f.namelist():
                            f.extract(names, source_path)
                except:
                    utils.ignore_error(os.remove, args=(zip_path,))
                    shutil.rmtree(source_path, ignore_errors=True)
                    raise

        self.start_hooks.append(init_source_code)
        return os.path.join(source_path, f"ws-scrcpy-{tag.lstrip('v')}")

    def on_starting(self):
        with open(self.get_app_path("config.yaml"), "wt") as fd:
            yaml.dump({
                "server": [{
                    "secure": False,
                    "port": self.get_config("WS_SCRCPY_PORT")
                }]
            }, fd)
