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
from linktools.cntr import BaseContainer, Integrations
from linktools.cntr.ext import Nginx, Flare, load_port_url
from linktools.core import ConfigField, PromptProvider
from linktools.decorator import cached_property


class Container(BaseContainer):

    @cached_property
    def configs(self):
        return dict(
            ARIA2_TAG="latest",
            ARIA2_DOMAIN=Nginx.domain(self),
            ARIA2_PORT=ConfigField(cast=int, default=0),
            ARIA2_RPC_SECRET=ConfigField(provider=PromptProvider(default="159753", cached=True)),
        )

    @cached_property
    def integrations(self) -> Integrations:
        return (
            Nginx.site(
                local_id="web",
                server_name=self.get_config_later("ARIA2_DOMAIN"),
                proxy="http://aria2-pro:6800",
                auth=False,
            ),
            Flare.container("aria2", "tools", load_port_url(self, "ARIA2_PORT", https=False), desc=""),
        )
