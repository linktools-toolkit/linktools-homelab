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
from typing import Iterable

import yaml

from linktools.cntr import SourceContainer, ExposeLink, EventContext
from linktools.core import ConfigField
from linktools.decorator import cached_property


class Container(SourceContainer):

    @cached_property
    def configs(self):
        return dict(
            WS_SCRCPY_TAG="master",
            WS_SCRCPY_URL="https://github.com/redroid-rockchip/ws-scrcpy/archive/refs/heads/{tag}.zip",
            WS_SCRCPY_PORT=ConfigField(cast=int, default=8000),
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_container(
                "ws-scrcpy", "cellphone", "ws-scrcpy",
                self.load_port_url("WS_SCRCPY_PORT", https=False)),
        ]

    @property
    def _source_url(self):
        tag = self.get_config("WS_SCRCPY_TAG")
        url = self.get_config("WS_SCRCPY_URL").format(tag=tag)
        return url

    @property
    def _source_path(self):
        tag = self.get_config("WS_SCRCPY_TAG")
        return f"ws-scrcpy-{tag.lstrip('v')}"

    def on_starting(self, context: EventContext):
        super().on_starting(context)

        with open(self.get_app_path("config.yaml"), "wt") as fd:
            yaml.dump({
                "server": [{
                    "secure": False,
                    "port": self.get_config("WS_SCRCPY_PORT")
                }]
            }, fd)
