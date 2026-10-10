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
from linktools.cntr.ext import Nginx, Flare, load_config_url
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["homelab"]

    @cached_property
    def configs(self):
        return dict(
            FNOS_DOMAIN=Nginx.domain(self, "fn"),
            FNOS_LOCAL_URL="http://10.10.10.1:5666",
            FNOS_DAV_LOCAL_URL="http://10.10.10.1:5005",
        )

    @cached_property
    def integrations(self) -> Integrations:
        return (
            Nginx.site(
                link=Flare.public("fnOS", "nas", "飞牛系统"),
                server_name=self.get_config_later("FNOS_DOMAIN"),
                template=self.get_source_path("nginx.conf"),
                auth=False,
            ),
            Flare.category("private")("fnOS", "nas", "飞牛系统", load_config_url(
                self, "FNOS_LOCAL_URL",
            )),
        )
