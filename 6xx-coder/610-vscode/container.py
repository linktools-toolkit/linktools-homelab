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
from pathlib import PurePosixPath
from typing import Any, Iterable

from linktools import utils
from linktools.core import Config
from linktools.cli import subcommand, subcommand_argument
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, ExposeLink, EventContext


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx", "coder"]

    @cached_property
    def configs(self):
        return dict(
            VSCODE_TAG="latest",
            VSCODE_DOMAIN=self.get_nginx_domain(),
            VSCODE_PORT=Config.Alias(type=int, default=0),
            VSCODE_PASSWORD=Config.Lazy(
                lambda cfg:
                Config.Prompt(cached=True)
                if not cfg.get("NGINX_AUTH_ENABLE")
                else ""
            ),
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("VS Code", "microsoftVisualStudioCode", "在线vscode", self.load_nginx_url(
                "VSCODE_DOMAIN",
                proxy_url="http://code-server:8080",
                auth_enable=True,
                auth_extra={
                    "acl_bypass": ["\\.(css|js)$"],
                }
            )),
            self.expose_container("VS Code", "microsoftVisualStudioCode", "在线vscode", self.load_port_url(
                "VSCODE_PORT",
                https=False
            )),
        ]

    @subcommand("install-extensions", help="Install vsix from https://marketplace.visualstudio.com/")
    @subcommand_argument("--copilot-chat", metavar="VERSION",
                         config=Config.Property(key="VSCODE_COPILOT_CHAT_VERSION") | Config.Prompt(always_ask=True),
                         help="https://github.com/microsoft/vscode-copilot-chat/releases")
    @subcommand_argument("--claude-code", metavar="VERSION",
                         config=Config.Property(key="VSCODE_CLAUDE_CODE_VERSION") | Config.Prompt(always_ask=True),
                         help="https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code")
    @subcommand_argument("--chatgpt", metavar="VERSION",
                         config=Config.Property(key="VSCODE_CHATGPT_VERSION") | Config.Prompt(always_ask=True),
                         help="https://marketplace.visualstudio.com/items?itemName=openai.chatgpt")
    @subcommand_argument("-f", "--force", help="force install")
    def on_exec_install_extensions(
        self,
        copilot_chat: str = "0.42.3",
        claude_code: str = "latest",
        chatgpt: str = "latest",
        force: bool = False
    ):
        extensions = {
            "GitHub.copilot-chat": {
                "version": copilot_chat,
                "url": "https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{publisher}/vsextensions/{name}/{version}/vspackage"
            },
            "Anthropic.claude-code": {
                "version": claude_code,
            },
            "openai.chatgpt": {
                "version": chatgpt,
            },
        }

        for key, info in extensions.items():
            publisher, name = key.split(".", 1)
            url = info.get("url", None)
            version = info.get("version")
            if not version:
                self.logger.warning(f"Extension {name} version is empty, skipped")
                continue

            if url:
                visx_name = f"{publisher}.{name}-{version}.vsix"
                visx_host_path = self.get_app_path("home", ".vsix")
                visx_docker_path = PurePosixPath("/workspace/.vsix")

                if force:
                    utils.remove_file(visx_host_path / visx_name)
                if not os.path.exists(visx_host_path / visx_name):
                    visx_url = url.format(name=name, publisher=publisher, version=version)
                    with self.manager.environ.get_url_file(visx_url) as file:
                        if not os.path.exists(visx_host_path / visx_name):
                            file.save(visx_host_path, visx_name)
                
                self.manager.create_docker_process(
                    "exec", self.get_service_name("code-server"),
                    "code-server", "--install-extension", visx_docker_path / visx_name
                ).check_call()

            else:
                ext_args = []
                if version in ("", "latest"):
                    ext_args.append(f"{publisher}.{name}")
                else:
                    ext_args.append(f"{publisher}.{name}@{version}")
                if force:
                    ext_args.append("--force")
                self.manager.create_docker_process(
                    "exec", self.get_service_name("code-server"),
                    "code-server", "--install-extension", *ext_args
                ).check_call()

    @cached_property
    def proxy_url(self):
        nginx = self.manager.containers["nginx"]
        if nginx.enable and self.get_config("NGINX_WILDCARD_DOMAIN"):
            domain: Any = self.get_config("VSCODE_DOMAIN")
            if domain:
                if self.get_config("NGINX_HTTPS_ENABLE"):
                    scheme = "https"
                    port = self.get_config("NGINX_HTTPS_PORT")
                else:
                    scheme = "http"
                    port = self.get_config("NGINX_HTTP_PORT")
                proxy_domain = domain.replace(".", "\\.")
                self.start_hooks.append(lambda: self.write_nginx_conf(
                    rf"~^(?<proxy_port>\d+).{proxy_domain}$",
                    proxy_name="proxy",
                    proxy_domain_name=f"{domain}_proxy",
                    proxy_url="http://code-server:8080/proxy/$proxy_port",
                    auth_enable=True,
                ))
                return utils.make_url(scheme, f"{{{{port}}}}.{domain}", port)
        return ""

    def on_prepare(self):
        if self.proxy_url:
            nginx = self.manager.containers["nginx"]
            domain = self.get_config("VSCODE_DOMAIN")
            nginx.ssl_domains.append(f"*.{domain}")

    def on_removed(self, context: "EventContext"):
        utils.remove_file(self.get_app_path("home", ".vsix"))
