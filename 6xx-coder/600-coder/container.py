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
from pathlib import Path

from linktools import utils
from linktools.cntr import BaseContainer, ExposeLink
from linktools.core import Config
from linktools.decorator import cached_property


class Container(BaseContainer):

    def _get_home_path(self, cfg: Config):
        try:
            import pwd
            passwd = pwd.getpwnam(cfg.get("DOCKER_USER"))
            return Path(passwd.pw_dir)
        except ImportError:
            return Path.home()

    def _get_git_name(self):
        try:
            return self.manager.create_process("git", "config", "--global", "user.name", capture_output=True).exec()
        except:
            return ""

    def _get_git_email(self):
        try:
            return self.manager.create_process("git", "config", "--global", "user.email", capture_output=True).exec()
        except:
            return ""

    @cached_property
    def configs(self):
        return dict(
            CODER_HOME_PATH=Config.Alias(type="path") | Config.Lazy(lambda cfg: self._get_home_path(cfg)),
            CODER_LLM_PATH=Config.Alias(type="path") | self.get_app_path("llm"),
            CODER_GIT_NAME=Config.Lazy(lambda cfg: self._get_git_name()),
            CODER_GIT_EMAIL=Config.Lazy(lambda cfg: self._get_git_email()),
            CODER_PROJECT_PATH=Config.Alias("PROJECT_PATH", type="path") | Config.Prompt(cached=True) | self.get_app_path("projects"),
        )

    @cached_property
    def base_home_files(self):
        result = dict()
        for name in (".ssh",):
            path = os.path.join(self.get_config("CODER_HOME_PATH"), name)
            if os.path.exists(path):
                result[name] = path
        return result

    @cached_property
    def home_files(self):
        result = dict(self.base_home_files)
        for name in (".codex", ".claude", ".cursor", ".gemini"):
            path = os.path.join(self.get_config("CODER_LLM_PATH"), name)
            self.start_hooks.append(functools.partial(os.makedirs, path, mode=0o755, exist_ok=True))
            self.start_hooks.append(functools.partial(self.manager.change_file_owner, path, self.get_config("DOCKER_USER"), recursive=False))
            result[name] = path
        return result
