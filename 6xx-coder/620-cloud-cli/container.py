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
import shutil
import zipfile
from typing import Iterable

from linktools import utils
from linktools.cntr import BaseContainer, ExposeLink
from linktools.core import Config
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx", "coder"]

    @cached_property
    def configs(self):
        return dict(
            CLOUD_CLI_TAG="v1.26.3",
            CLOUD_CLI_URL="https://github.com/siteboon/claudecodeui/archive/refs/tags/{tag}.zip",
            CLOUD_CLI_DOMAIN=self.get_nginx_domain(),
            CLOUD_CLI_PORT=Config.Alias(type=int, default=0),
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("CloudCLI", "messageOutline", "Cloud CLI", self.load_nginx_url(
                "CLOUD_CLI_DOMAIN",
                proxy_url="http://cloud-cli:3001",
                auth_enable=True,
                auth_extra={
                    "acl_bypass": ["\\.(css|js)$"],
                }
            )),
            self.expose_container("CloudCLI", "messageOutline", "Cloud CLI", self.load_port_url(
                "CLOUD_CLI_PORT",
                https=False
            )),
        ]

    @cached_property
    def code_path(self):
        tag = self.get_config("CLOUD_CLI_TAG")
        url = self.get_config("CLOUD_CLI_URL").format(tag=tag)

        zip_path = self.get_app_path("source", f"{tag}-{utils.get_md5(url)}.zip")
        source_path = str(zip_path) + ".unzip"

        def init_source_code():
            if not os.path.isdir(source_path):
                file = self.manager.environ.get_url_file(url)
                file.save(zip_path.parent, zip_path.name)
                os.makedirs(source_path, exist_ok=True)
                try:
                    with zipfile.ZipFile(zip_path) as f:
                        for names in f.namelist():
                            f.extract(names, source_path)
                except:
                    utils.ignore_errors(os.remove, args=(zip_path,))
                    shutil.rmtree(source_path, ignore_errors=True)
                    raise

        self.start_hooks.append(init_source_code)
        return os.path.join(source_path, f"claudecodeui-{tag.lstrip('v')}")

    def on_removed(self):
        utils.remove_file(self.get_app_path("source"))
