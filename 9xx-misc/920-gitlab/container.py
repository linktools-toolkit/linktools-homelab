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

from linktools.cli import subcommand
from linktools.cntr import BaseContainer, ExposeLink
from linktools.core import Config
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            GITLAB_TAG="latest",
            GITLAB_DOMAIN=self.get_nginx_domain(),
            GITLAB_SSH_PORT=Config.Prompt(type=int, cached=True) | 3001,
            GITLAB_ROOT_PASSWORD=Config.Prompt(type=str, cached=True) | "xxx123456xxxx",  # gitlab默认root密码
            GITLAB_DB_HOST="gitlab-postgres",
            GITLAB_DB_PORT="5432",
            GITLAB_DB_DATABASE="gitlab1",
            GITLAB_DB_USERNAME="gitlab2",
            GITLAB_DB_PASSWORD="gitlab3",
            GITLAB_REDIS_HOST="gitlab-redis",
            GITLAB_REDIS_PORT="6379",
            GITLAB_REDIS_PASSWORD="gitlab_redis_pass",
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("Gitlab", "git", "代码仓库管理", self.load_nginx_url(
                "GITLAB_DOMAIN",
                proxy_conf=self.get_source_path("nginx.conf"),
            )),
        ]

    @subcommand("fix", help="fix permissions")
    def on_exec_fix(self):
        self.manager.create_docker_process("exec", self.get_service_name("gitlab"), "update-permissions").check_call()
        self.manager.create_docker_process("restart", self.get_service_name("gitlab")).check_call()

    def on_started(self):
        self.manager.create_docker_process("exec", self.get_service_name("gitlab"), "chown", "-R", "git:git", "/var/opt/gitlab").check_call()
        self.manager.create_docker_process("exec", self.get_service_name("gitlab"), "chmod", "-R", "777", "/var/opt/gitlab").check_call()
        # self.manager.create_docker_process("exec", self.get_service_name("gitlab"), "update-permissions").check_call()
        # self.manager.create_docker_process("restart", self.get_service_name("gitlab")).check_call()
