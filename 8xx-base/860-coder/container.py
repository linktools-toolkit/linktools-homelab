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

import os
from pathlib import Path

from linktools.cntr import BaseContainer
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
            return self.manager.create_process(
                "git", "config", "--global", "user.name", 
                capture_output=True
            ).exec()
        except:
            return ""

    def _get_git_email(self):
        try:
            return self.manager.create_process(
                "git", "config", "--global", "user.email", 
                capture_output=True
            ).exec()
        except:
            return ""

    @cached_property
    def configs(self):
        return dict(
            CODER_HOME_PATH=Config.Alias(type="path") | Config.Lazy(lambda cfg: self._get_home_path(cfg)),
            CODER_GIT_NAME=Config.Lazy(lambda cfg: self._get_git_name()),
            CODER_GIT_EMAIL=Config.Lazy(lambda cfg: self._get_git_email()),
            CODER_NPM_REGISTRY="https://registry.npmmirror.com",
            CODER_PIP_REGISTRY="https://pypi.org/simple/",
            CODER_PROJECT_PATH=Config.Alias("PROJECT_PATH", type="path") |
                               Config.Prompt(cached=True) |
                               self.get_app_path("projects")
        )

    @cached_property
    def home_files(self):
        result = dict()
        for name in (".ssh",):
            path = os.path.join(self.get_config("CODER_HOME_PATH"), name)
            if os.path.isdir(path):
                result[name] = path
        return result

    @cached_property
    def project_files(self):
        result = dict()
        result[""] = self.get_config("CODER_PROJECT_PATH")
        return result
