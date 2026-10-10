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
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, Integrations
from linktools.cntr.ext import Nginx, Flare, load_config_url


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
        return (
            Nginx.site(
                local_id="web",
                expose=Flare.public("OpenMediaVault", "nas", "OMV系统"),
                server_name=self.get_config_later("OMV_DOMAIN"),
                proxy=self.get_config_later("OMV_LOCAL_URL"),
                auth=False,
            ),
            Flare.category("private")("OpenMediaVault", "nas", "OMV系统", load_config_url(
                self, "OMV_LOCAL_URL"
            )),
        )
