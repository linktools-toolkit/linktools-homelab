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
from pathlib import Path

from linktools.cntr import BaseContainer, ExposeLink
from linktools.core import Config
from linktools.decorator import cached_property


class Container(BaseContainer):

    @classmethod
    def _get_ssh_path(cls, cfg: Config):
        try:
            import pwd
            passwd = pwd.getpwnam(cfg.get("DOCKER_USER"))
            return Path(passwd.pw_dir).joinpath(".ssh")
        except ImportError:
            return Path.home().joinpath(".ssh")

    @cached_property
    def configs(self):
        return dict(
            CODER_SSH_PATH=Config.Alias(type="path") | Config.Lazy(lambda cfg: self._get_ssh_path(cfg)),
            CODER_LLM_PATH=Config.Alias(type="path") | self.get_app_path("llm"),
            CODER_PROJECT_PATH=Config.Alias("PROJECT_PATH", type="path") | Config.Prompt(cached=True) | self.get_app_path("projects"),
        )
