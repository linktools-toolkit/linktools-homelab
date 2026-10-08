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
from linktools.cntr import BaseContainer, Integrations, NginxSite


class Container(BaseContainer):

    @cached_property
    def configs(self):
        return dict(
            IT_TOOLS_TAG="latest",
            IT_TOOLS_DOMAIN=self.get_nginx_domain(),
            IT_TOOLS_PORT=ConfigField(cast=int, default=0)
        )

    @cached_property
    def integrations(self) -> Integrations:
        return {
            "nginx": {
                "web": NginxSite(
                    expose=self.expose_public("IT Tools", "tools", "it工具集"),
                    server_name=self.get_config_later("IT_TOOLS_DOMAIN"),
                    proxy="http://it-tools",
                    auth_bypass=(r"\.(css|js|webmanifest)$",),
                    auth_rule={"policy": "one_factor"},
                ),
            },
            "flare": {
                "regex_tester": self.expose_other("正则表达式测试", "regex", "", self.load_nginx_url("web", "regex-tester")),
                "regex_memo": self.expose_other("正则表达式手册", "regex", "", self.load_nginx_url("web", "regex-memo")),
                "json_prettify": self.expose_other("在线json解析", "codeJson", "", self.load_nginx_url("web", "json-prettify")),
                "dns_lookup": self.expose_other("DNS查询", "dns", "", "https://tool.chinaz.com/dns/"),
                "icons": self.expose_other("图标下载", "progressDownload", "", "https://materialdesignicons.com/"),
                "direct": self.expose_container("IT Tools", "tools", "it工具集", self.load_port_url("IT_TOOLS_PORT", https=False)),
            },
        }
