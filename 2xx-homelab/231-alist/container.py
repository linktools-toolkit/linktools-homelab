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
from linktools.core import Config
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx", "storage"]

    @cached_property
    def configs(self):
        return dict(
            ALIST_TAG="latest",
            ALIST_DATA_PATH=Config.Alias("STORAGE_USER_PATH", type="path"),
            ALIST_ADMIN_PASSWORD=Config.Prompt(cached=True) | utils.make_uuid()[:12],
            ALIST_DOMAIN=self.get_nginx_domain(),
            ALIST_PORT=Config.Alias(type=int) | 0,
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
