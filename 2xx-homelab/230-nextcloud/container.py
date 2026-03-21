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
import random
import string
from typing import Iterable

from linktools.core import Config
from linktools.cli import subcommand
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, ExposeLink


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx", "storage", "download"]

    @cached_property
    def configs(self):
        return dict(
            NEXTCLOUD_TAG="latest",
            NEXTCLOUD_DOMAIN=self.get_nginx_domain(),
            NEXTCLOUD_MYSQL_ROOT_PASSWORD="root_password",
            NEXTCLOUD_MYSQL_DATABASE="nas",
            NEXTCLOUD_MYSQL_USER="nas",
            NEXTCLOUD_MYSQL_PASSWORD="password",
            NEXTCLOUD_ONLYOFFICE_ENABLED=Config.Alias(type=bool, default=False),
            NEXTCLOUD_ONLYOFFICE_SECRET=Config.Alias(default="".join(random.sample(string.ascii_letters + string.digits, 12)), cached=True),
            NEXTCLOUD_MAINTENANCE_WINDOW_START=Config.Alias(type=int, default=2),
            NEXTCLOUD_PHP_MEMORY_LIMIT=None,
            NEXTCLOUD_PHP_UPLOAD_LIMIT=None,
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("Nextcloud", "cloudDownloadOutline", "私人网盘", self.load_nginx_url(
                "NEXTCLOUD_DOMAIN",
                proxy_conf=self.get_source_path("nginx.conf"),
            )),
        ]

    @subcommand("scan", help="scan all files")
    def on_exec_scan(self):
        self.manager.create_docker_process(
            "exec", self.get_service_name("nextcloud"), "./occ", "files:scan", "--all"
        ).check_call()
