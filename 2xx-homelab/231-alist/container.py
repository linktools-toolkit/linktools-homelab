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
from linktools.cntr import BaseContainer, ExposeLink
from linktools.core import ConfigField, AliasProvider, LazyProvider
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            ALIST_TAG="latest",
            ALIST_DATA_PATH=ConfigField(cast="path", provider=AliasProvider("DOCKER_USER_DATA_PATH")),
            ALIST_ADMIN_PASSWORD=ConfigField(provider=LazyProvider(lambda r: utils.make_uuid()[:12], cached=True)),
            ALIST_DOMAIN=self.get_nginx_domain(),
            ALIST_PORT=ConfigField(cast=int, default=0),
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_container("Alist", "folderSync", "", self.load_port_url(
                "ALIST_PORT",
                https=False,
            )),
            self.expose_public("Alist", "folderSync", "", self.load_nginx_url(
                "ALIST_DOMAIN",
                proxy_url="http://alist:5244",
            )),
        ]
