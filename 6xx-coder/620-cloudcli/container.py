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

from linktools.cntr import SourceContainer, ExposeLink
from linktools.core import Config
from linktools.decorator import cached_property


class Container(SourceContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx", "coder"]

    @cached_property
    def configs(self):
        return dict(
            CLOUD_CLI_TAG="main",
            CLOUD_CLI_URL="https://github.com/siteboon/claudecodeui/archive/refs/heads/{tag}.zip",
            CLOUD_CLI_DOMAIN=self.get_nginx_domain(),
            CLOUD_CLI_PORT=Config.Alias(type=int, default=0),
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("CloudCLI", "messageOutline", "Cloud CLI", self.load_nginx_url(
                "CLOUD_CLI_DOMAIN",
                proxy_url="http://cloudcli:3001",
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

    @property
    def _source_url(self):
        tag = self.get_config("CLOUD_CLI_TAG")
        url = self.get_config("CLOUD_CLI_URL").format(tag=tag)
        return url

    @property
    def _source_path(self):
        tag = self.get_config("CLOUD_CLI_TAG")
        return f"claudecodeui-{tag.lstrip('v')}"

    def on_prepare(self):
        coder = self.manager.containers["coder"]
        coder.install_modules[self.get_service_name("cloudcli")] = [
            {"type": "npm", "module": "task-master-ai@latest"},
            {"type": "shell", "module": "curl -fsSL https://claude.ai/install.sh | bash"},
            {"type": "npm", "module": "@openai/codex@latest"},
            {"type": "npm", "module": "@google/gemini-cli@latest"},
            {"type": "npm", "module": "npx@latest"},
            {"type": "shell", "module": "curl https://cursor.com/install -fsS | bash"},
        ]
