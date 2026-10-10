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

from linktools.core import ConfigField
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, Integrations
from linktools.cntr.ext import Nginx, Flare, load_nginx_url, load_port_url


class Container(BaseContainer):

    @cached_property
    def configs(self):
        return dict(
            IT_TOOLS_TAG="latest",
            IT_TOOLS_DOMAIN=Nginx.domain(self),
            IT_TOOLS_PORT=ConfigField(cast=int, default=0)
        )

    @cached_property
    def integrations(self) -> Integrations:
        return (
            Nginx.site(
                local_id="web",
                expose=Flare.public("IT Tools", "tools", "it工具集"),
                server_name=self.get_config_later("IT_TOOLS_DOMAIN"),
                proxy="http://it-tools",
                auth_bypass=(r"\.(css|js|webmanifest)$",),
                auth_rule={"policy": "one_factor"},
            ),
            Flare.category("other")("正则表达式测试", "regex", "", load_nginx_url(self, "web", "regex-tester")),
            Flare.category("other")("正则表达式手册", "regex", "", load_nginx_url(self, "web", "regex-memo")),
            Flare.category("other")("在线json解析", "codeJson", "", load_nginx_url(self, "web", "json-prettify")),
            Flare.category("other")("DNS查询", "dns", "", "https://tool.chinaz.com/dns/"),
            Flare.category("other")("图标下载", "progressDownload", "", "https://materialdesignicons.com/"),
            Flare.container("IT Tools", "tools", load_port_url(self, "IT_TOOLS_PORT", https=False), desc="it工具集"),
        )
