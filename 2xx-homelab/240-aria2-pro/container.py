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
from linktools.cntr import BaseContainer, Integrations, NginxSite
from linktools.core import ConfigField, PromptProvider
from linktools.decorator import cached_property


class Container(BaseContainer):

    @cached_property
    def configs(self):
        return dict(
            ARIA2_TAG="latest",
            ARIA2_DOMAIN=self.get_nginx_domain(),
            ARIA2_PORT=ConfigField(cast=int, default=0),
            ARIA2_RPC_SECRET=ConfigField(provider=PromptProvider(default="159753", cached=True)),
        )

    @cached_property
    def integrations(self) -> Integrations:
        return {
            "nginx": {
                "web": NginxSite(
                    server_name=self.get_config_later("ARIA2_DOMAIN"),
                    proxy="http://aria2-pro:6800",
                    auth=False,
                ),
            },
            "flare": {
                "direct": self.expose_container("aria2", "tools", "", self.load_port_url("ARIA2_PORT", https=False)),
            },
        }
