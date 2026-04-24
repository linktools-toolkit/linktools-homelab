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

    @cached_property
    def configs(self):
        return dict(
            IT_TOOLS_TAG="latest",
            IT_TOOLS_DOMAIN=self.get_nginx_domain(),
            IT_TOOLS_PORT=Config.Alias(type=int, default=0)
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_other("正则表达式测试", "regex", "", self.load_exist_nginx_url("IT_TOOLS_DOMAIN", "regex-tester")),
            self.expose_other("正则表达式手册", "regex", "", self.load_exist_nginx_url("IT_TOOLS_DOMAIN", "regex-memo")),
            self.expose_other("在线json解析", "codeJson", "", self.load_exist_nginx_url("IT_TOOLS_DOMAIN", "json-prettify")),
            self.expose_other("DNS查询", "dns", "", "https://tool.chinaz.com/dns/"),
            self.expose_other("图标下载", "progressDownload", "", "https://materialdesignicons.com/"),

            self.expose_container("IT Tools", "tools", "it工具集", self.load_port_url("IT_TOOLS_PORT", https=False)),
            self.expose_public("IT Tools", "tools", "it工具集", self.load_nginx_url(
                "IT_TOOLS_DOMAIN",
                proxy_url="http://it-tools",
                auth_enable=True,
                auth_extra={
                    "acl_bypass": ["\\.(css|js|webmanifest)$"],
                    "acl_rule": {
                        "policy": "one_factor",
                    }
                }
            )),
        ]
