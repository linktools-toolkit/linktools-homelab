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

from linktools.core import Config
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, ExposeLink


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx", "coder"]

    @cached_property
    def configs(self):
        return dict(
            VSCODE_TAG="latest",
            VSCODE_DOMAIN=self.get_nginx_domain(),
            VSCODE_PORT=Config.Alias(type=int, default=0),
            VSCODE_PASSWORD=Config.Lazy(
                lambda cfg:
                Config.Prompt(cached=True)
                if not cfg.get("NGINX_AUTH_ENABLE")
                else ""
            ),
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("VS Code", "microsoftVisualStudioCode", "在线vscode", self.load_nginx_url(
                "VSCODE_DOMAIN",
                proxy_url="http://code-server:8080",
                auth_enable=True,
                auth_extra={
                    "acl_bypass": ["\\.(css|js)$"],
                }
            )),
            self.expose_container("VS Code", "microsoftVisualStudioCode", "在线vscode", self.load_port_url(
                "VSCODE_PORT",
                https=False
            )),
        ]
