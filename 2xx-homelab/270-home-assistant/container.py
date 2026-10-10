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

from linktools.cntr import BaseContainer, Integrations
from linktools.cntr.ext import Nginx, Flare, load_port_url
from linktools.core import ConfigField
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            HOME_ASSISTANT_TAG="stable",
            HOME_ASSISTANT_DOMAIN=Nginx.domain(self, "homeassistant"),
            HOME_ASSISTANT_PORT=ConfigField(cast=int, default=8123),
        )

    @cached_property
    def integrations(self) -> Integrations:
        return (
            Nginx.site(
                link=Flare.public("HomeAssistant", "homeAssistant", "Home Assistant"),
                server_name=self.get_config_later("HOME_ASSISTANT_DOMAIN"),
                proxy="http://home-assistant:8123",
                auth=False,
            ),
            Flare.container("HomeAssistant", "homeAssistant", load_port_url(
                self, "HOME_ASSISTANT_PORT",
                https=False,
            ), desc="Home Assistant"),
        )
