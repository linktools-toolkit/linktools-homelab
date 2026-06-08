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

from linktools import utils
from linktools.cli import subcommand
from linktools.core import Config
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, ExposeLink


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx", "coder", "ai"]

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

    @cached_property
    def proxy_url(self):
        nginx = self.manager.containers["nginx"]
        if nginx.enable and self.get_config("NGINX_WILDCARD_DOMAIN"):
            domain = self.get_config("VSCODE_DOMAIN")
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
                    proxy_conf=self.get_source_path("proxy.conf"),
                    auth_enable=True,
                ))
                return utils.make_url(scheme, f"{{{{port}}}}.{domain}", port)
        return ""

    def on_prepare(self):
        if self.proxy_url:
            nginx = self.manager.containers["nginx"]
            domain = self.get_config("VSCODE_DOMAIN")
            nginx.append_ssl_domains(f"*.{domain}")

    @subcommand("install", help="install modules into the running container")
    def on_exec_install(self):
        self.logger.info("Install cc-switch-cli to `code-server`")
        self.manager.create_docker_process(
            "exec", "-it", self.get_service_name("code-server"),
            "sh", "-c", "curl -fsSL https://github.com/SaladDay/cc-switch-cli/releases/latest/download/install.sh | bash",
        ).check_call()
        self.manager.create_docker_process(
            "exec", "-it", self.get_service_name("code-server"),
            "cc-switch", "completions", "install", "--activate", "--shell", "bash"
        ).check_call()
