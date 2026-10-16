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

from linktools.core import ConfigField, ConfigRef
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, Integrations
from linktools.cntr.ext import Nginx, Flare, load_port_url, Authelia, endpoint


class Container(BaseContainer):

    @cached_property
    def fields(self):
        return dict(
            IT_TOOLS_TAG="latest",
            IT_TOOLS_DOMAIN=Nginx.domain(self),
            IT_TOOLS_PORT=ConfigField(cast=int, default=0)
        )

    @cached_property
    def integrations(self) -> Integrations:
        return endpoint(
            self,
            domain=ConfigRef("IT_TOOLS_DOMAIN"),
            proxy="http://it-tools",
            auth_bypass=(r"\.(css|js|webmanifest)$",),
            extensions=[
                Authelia.access(
                    policy="one_factor",
                ),
                Flare.links(
                    Flare.public(),
                    Flare.category("other")(
                        name="正则表达式测试",
                        icon="regex",
                        desc="",
                        url="{base_url}/regex-tester",
                    ),
                    Flare.category("other")(
                        name="正则表达式手册",
                        icon="regex",
                        desc="",
                        url="{base_url}/regex-memo",
                    ),
                    Flare.category("other")(
                        name="在线json解析",
                        icon="codeJson",
                        desc="",
                        url="{base_url}/json-prettify",
                    ),
                    Flare.category("other")(
                        name="DNS查询",
                        icon="dns",
                        desc="",
                        url="https://tool.chinaz.com/dns/",
                    ),
                    Flare.category("other")(
                        name="图标下载",
                        icon="progressDownload",
                        desc="",
                        url="https://materialdesignicons.com/",
                    ),
                    Flare.container(
                        url=load_port_url(ConfigRef("IT_TOOLS_PORT"), https=False),
                    ),
                    name="IT Tools",
                    icon="tools",
                    desc="it工具集",
                ),
            ],
        )
