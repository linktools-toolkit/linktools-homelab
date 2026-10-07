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

from linktools.cntr import BaseContainer, ExposeLink, NginxSite
from linktools.core import ConfigField
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            DSM_TAG="latest",
            DSM_DOMAIN="",
            DSM_PORT=ConfigField(cast=int, default=5000),
            DSM_DISK_FMT="qcow2",
            DSM_DISK_SIZE="6G",
        )

    @cached_property
    def integrations(self) -> "dict[str, dict[str, NginxSite]]":
        return {
            "nginx": {
                "web": NginxSite(
                    server_name=self.get_config_later("DSM_DOMAIN"),
                    proxy="http://dsm:5000",
                    auth=False,
                ),
            },
        }

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("DSM", "nas", "群晖系统", self.load_nginx_url("web")),
            self.expose_private("DSM", "nas", "群晖系统", self.load_port_url(
                "DSM_PORT",
                https=False,
            )),
        ]
