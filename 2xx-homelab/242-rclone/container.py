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

from linktools import utils
from linktools.cli import subcommand, subcommand_argument
from linktools.cntr import BaseContainer
from linktools.core import Config
from linktools.decorator import cached_property


class Container(BaseContainer):

    @cached_property
    def configs(self):
        return dict(
            RCLONE_TAG="latest",
            ALIST_DATA_PATH=Config.Prompt(cached=True, type="path") | self.get_app_data_path("data"),
            ALIST_ADMIN_PASSWORD=Config.Prompt(cached=True) | utils.make_uuid()[:12],
            ALIST_DOMAIN=self.get_nginx_domain(),
            ALIST_PORT=Config.Alias(type=int) | 0,
        )

    @subcommand("config", help="exec rclone config", prefix_chars=chr(1))
    @subcommand_argument("args", nargs="...", metavar="ARGS", help="rclone config args")
    def on_exec_rclone_config(self, args):
        service = self.choose_service()
        name = service.get("container_name")
        self.manager.create_docker_process(
            "exec", "-it", name,
            "rclone", "config", *args,
        ).call()

    @subcommand("crontab", help="exec crontab", prefix_chars=chr(1))
    @subcommand_argument("args", nargs="...", metavar="ARGS", help="crontab args")
    def on_exec_crontab(self, args):
        service = self.choose_service()
        name = service.get("container_name")
        self.manager.create_docker_process(
            "exec", "-it", name,
            "crontab", *args,
        ).call()
