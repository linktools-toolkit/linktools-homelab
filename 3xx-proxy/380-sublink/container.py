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

from linktools.cntr import BaseContainer, ExposeLink
from linktools.core import ConfigField, AliasProvider
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            SUBLINK_TAG="latest",
            SUBLINK_DOMAIN=self.get_nginx_domain(),
            SUBLINK_PORT=ConfigField(cast=int, default=0),
            SUBLINK_API_KEY="",
            SUBLINK_ADMIN_PASSWORD="123456",
            SUBLINK_ADMIN_PASSWORD_REST=ConfigField(provider=AliasProvider("SUBLINK_ADMIN_PASSWORD")),
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("SublinkPro", "link", "代理订阅管理", self.load_nginx_url(
                "SUBLINK_DOMAIN",
                proxy_conf=self.get_source_path("nginx.conf"),
                auth_enable=True
            )),
            self.expose_container("SublinkPro", "link", "代理订阅管理", self.load_port_url(
                "SUBLINK_PORT",
                https=False
            )),
        ]
