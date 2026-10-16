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

from linktools import utils
from linktools.core import ConfigRef
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, Integrations
from linktools.cntr.ext import Flare, load_config_url, endpoint


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["homelab", "nextcloud", "qbittorrent"]

    @cached_property
    def configs(self):
        return dict(
            OMV_DOMAIN="",
            OMV_LOCAL_URL="http://10.10.10.1:80",
        )

    @cached_property
    def integrations(self) -> Integrations:
        return endpoint(
            self,
            domain=ConfigRef("OMV_DOMAIN"),
            proxy=ConfigRef("OMV_LOCAL_URL"),
            auth=False,
            extensions=[
                Flare.links(
                    Flare.public(),
                    Flare.category("private")(
                        url=load_config_url(ConfigRef("OMV_LOCAL_URL", type=str)),
                    ),
                    name="OpenMediaVault",
                    icon="nas",
                    desc="OMV系统",
                ),
            ],
        )
