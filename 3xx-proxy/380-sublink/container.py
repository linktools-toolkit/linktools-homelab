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
from linktools.cntr.ext import Nginx, Flare, load_port_url, endpoint
from linktools.core import ConfigField, ConfigRef
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            SUBLINK_TAG="latest",
            SUBLINK_DOMAIN=Nginx.domain(self),
            SUBLINK_PORT=ConfigField(cast=int, default=0),
            SUBLINK_API_KEY="",
            SUBLINK_ADMIN_PASSWORD="123456",
        )

    @cached_property
    def integrations(self) -> Integrations:
        return endpoint(
            self,
            domain=ConfigRef("SUBLINK_DOMAIN"),
            template=self.get_source_path("nginx.conf"),
            auth=None,
            waf_bypass=(r"^/api/v1/script/",),
            extensions=[
                Flare.links(
                    Flare.public(),
                    Flare.container(
                        url=load_port_url(ConfigRef("SUBLINK_PORT", type=int, default=0), https=False),
                    ),
                    name="SublinkPro",
                    icon="link",
                    desc="代理订阅管理",
                ),
            ],
        )
