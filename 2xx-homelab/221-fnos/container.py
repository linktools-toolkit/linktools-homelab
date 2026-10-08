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

from linktools.cntr import BaseContainer, Integrations, NginxSite
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["homelab"]

    @cached_property
    def configs(self):
        return dict(
            FNOS_DOMAIN=self.get_nginx_domain("fn"),
            FNOS_LOCAL_URL="http://10.10.10.1:5666",
            FNOS_DAV_LOCAL_URL="http://10.10.10.1:5005",
        )

    @cached_property
    def integrations(self) -> Integrations:
        return {
            "nginx": {
                "web": NginxSite(
                    expose=self.expose_public("fnOS", "nas", "飞牛系统"),
                    server_name=self.get_config_later("FNOS_DOMAIN"),
                    template=self.get_source_path("nginx.conf"),
                    auth=False,
                ),
            },
            "flare": {
                "private": self.expose_private("fnOS", "nas", "飞牛系统", self.load_config_url(
                    "FNOS_LOCAL_URL",
                )),
            },
        }
