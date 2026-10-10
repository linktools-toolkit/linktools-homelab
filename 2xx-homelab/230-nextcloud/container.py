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

from linktools.core import ConfigField, LazyProvider
from linktools.cli import subcommand
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, Integrations
from linktools.cntr.ext import Nginx, Flare


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            NEXTCLOUD_TAG="latest",
            NEXTCLOUD_DOMAIN=Nginx.domain(self),
            NEXTCLOUD_MYSQL_ROOT_PASSWORD="root_password",
            NEXTCLOUD_MYSQL_DATABASE="nas",
            NEXTCLOUD_MYSQL_USER="nas",
            NEXTCLOUD_MYSQL_PASSWORD="password",
            NEXTCLOUD_ONLYOFFICE_ENABLED=ConfigField(cast=bool, default=False),
            NEXTCLOUD_ONLYOFFICE_SECRET=ConfigField(provider=LazyProvider(
                lambda r: "".join(random.sample(string.ascii_letters + string.digits, 12)), cached=True,
            )),
            NEXTCLOUD_MAINTENANCE_WINDOW_START=ConfigField(cast=int, default=2),
            NEXTCLOUD_PHP_MEMORY_LIMIT=None,
            NEXTCLOUD_PHP_UPLOAD_LIMIT=None,
        )

    @cached_property
    def integrations(self) -> Integrations:
        return (
            Nginx.site(
                link=Flare.public("Nextcloud", "cloudDownloadOutline", "私人网盘"),
                server_name=self.get_config_later("NEXTCLOUD_DOMAIN"),
                template=self.get_source_path("nginx.conf"),
                auth=False,
            ),
        )

    @subcommand("scan", help="scan all files")
    def on_exec_scan(self):
        self.manager.runtime.create_docker_process(
            "exec", self.get_service_name("nextcloud"), "./occ", "files:scan", "--all"
        ).check_call()
