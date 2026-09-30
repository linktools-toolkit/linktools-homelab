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
import functools
import os

from linktools.cntr import BaseContainer
from linktools.core import ConfigField
from linktools.decorator import cached_property


class Container(BaseContainer):

    @cached_property
    def configs(self):
        return dict(
            AI_HOME_PATH=ConfigField(cast="path", default=self.get_app_path("home")),
        )

    @cached_property
    def home_files(self):
        result = {}
        for name in (".codex", ".claude", ".cursor", ".gemini", ".cc-switch"):
            path = os.path.join(self.get_config("AI_HOME_PATH"), name)
            self.start_hooks.append(functools.partial(os.makedirs, path, mode=0o755, exist_ok=True))
            self.start_hooks.append(functools.partial(self.manager.runtime.chown, path, self.get_config("DOCKER_USER"), recursive=False))
            result[name] = path
        return result
