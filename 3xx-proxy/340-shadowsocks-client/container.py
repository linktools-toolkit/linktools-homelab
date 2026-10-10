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

import json

from linktools.cntr import OperationContext, BaseContainer
from linktools.core import ConfigField, PromptProvider
from linktools.decorator import cached_property


class Container(BaseContainer):

    @cached_property
    def configs(self):
        return dict(
            SHADOWSOCKS_CLIENT_TAG="latest",
            SHADOWSOCKS_CLIENT_PORT=ConfigField(cast=int, provider=PromptProvider(default=1080, cached=True)),
            SHADOWSOCKS_SERVER_HOST=ConfigField(provider=PromptProvider(cached=True)),
            SHADOWSOCKS_SERVER_PORT=ConfigField(cast=int, provider=PromptProvider(cached=True)),
            SHADOWSOCKS_SERVER_PASSWORD=ConfigField(provider=PromptProvider(cached=True)),
            SHADOWSOCKS_SERVER_METHOD=ConfigField(provider=PromptProvider(default="aes-256-gcm", cached=True)),
        )

    def on_starting(self, context: OperationContext):
        context.write_files(self, {
            "config.json": self.render_template(self.get_source_path("config.json")),
        })

    def on_check(self, context: OperationContext):
        json.loads(context.file_path(self, "config.json").read_text(encoding="utf-8"))
