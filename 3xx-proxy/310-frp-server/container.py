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

from configparser import RawConfigParser

from linktools import utils
from linktools.cntr import OperationContext, BaseContainer
from linktools.core import ConfigField, PromptProvider
from linktools.decorator import cached_property


class Container(BaseContainer):

    @cached_property
    def configs(self):
        return dict(
            FRPS_TAG="latest",
            FRPS_BIND_PORT=ConfigField(cast=int, provider=PromptProvider(default=7000, cached=True)),
            FRPS_BIND_TOKEN=ConfigField(provider=PromptProvider(default=utils.make_uuid()[:12], cached=True)),
            FRPS_VHOST_HTTP_PORT=ConfigField(cast=int, provider=PromptProvider(default=80, cached=True)),
            FRPS_VHOST_HTTPS_PORT=ConfigField(cast=int, provider=PromptProvider(default=443, cached=True)),
        )

    def on_starting(self, context: OperationContext):
        context.write_files(self, {
            "frps.ini": self.render_template(self.get_source_path("frps.ini")),
        })

    def on_check(self, context: OperationContext):
        parser = RawConfigParser()
        parser.read_string(context.file_path(self, "frps.ini").read_text(encoding="utf-8"))
