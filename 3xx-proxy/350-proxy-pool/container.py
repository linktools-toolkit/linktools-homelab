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
from typing import Any, Iterable

from linktools.cntr import BaseContainer, NginxSite
from linktools.core import ConfigField
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            PROXY_POOL_TAG="latest",
            PROXY_POOL_DOMAIN=self.get_nginx_domain(),
            PROXY_POOL_PORT=ConfigField(cast=int, default=0),
        )

    @cached_property
    def integrations(self) -> "dict[str, dict[str, Any]]":
        return {
            "nginx": {
                "web": NginxSite(
                    server_name=self.get_config_later("PROXY_POOL_DOMAIN"),
                    proxy="http://proxy-pool:5010",
                    auth=False,
                ),
            },
            "flare": {
                "public": self.expose_public("Proxy Pool", "tools", "代理池", self.load_nginx_url("web")),
                "direct": self.expose_container("Proxy Pool", "tools", "代理池", self.load_port_url(
                    "PROXY_POOL_PORT",
                    https=False
                )),
            },
        }
