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

from linktools.cntr import BaseContainer
from linktools.core import Config
from linktools.decorator import cached_property


class Container(BaseContainer):

    @cached_property
    def configs(self):
        return dict(
            SHADOWSOCKS_CLIENT_TAG="latest",
            SHADOWSOCKS_CLIENT_PORT=Config.Prompt(default=1080, type=int, cached=True),
            SHADOWSOCKS_SERVER_HOST=Config.Prompt(cached=True),
            SHADOWSOCKS_SERVER_PORT=Config.Prompt(type=int, cached=True),
            SHADOWSOCKS_SERVER_PASSWORD=Config.Prompt(cached=True),
            SHADOWSOCKS_SERVER_METHOD=Config.Prompt(default="aes-256-gcm", cached=True),
        )

    def on_starting(self):
        self.render_template(
            self.get_source_path("config.json"),
            self.get_app_path("config.json", create_parent=True),
        )
