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
import json
import re
import shutil
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
        # self.logger.info("Install cc-switch-cli to `code-server`")
        # self.manager.create_docker_process(
        #     "exec", "-it", self.get_service_name("code-server"),
        #     "sh", "-c", "curl -fsSL https://github.com/SaladDay/cc-switch-cli/releases/latest/download/install.sh | bash",
        # ).check_call()
        # self.manager.create_docker_process(
        #     "exec", "-it", self.get_service_name("code-server"),
        #     "cc-switch", "completions", "install", "--activate", "--shell", "bash"
        # ).check_call()

        extensions = (
            "yzhang.markdown-all-in-one",
            "shd101wyy.markdown-preview-enhanced",
            "bierner.markdown-mermaid",
            "ms-vscode.live-server",
            "Anthropic.claude-code",
            "openai.chatgpt",
            # "google.geminicodeassist",
        )
        for extension in extensions:
            self.logger.info(f"Install {extension} to `code-server`")
            self.manager.create_docker_process(
                "exec", "-it", self.get_service_name("code-server"),
                "code-server", "--install-extension", extension,
            ).check_call()

        settings_path = self.get_app_path("home/.local/share/code-server/User/settings.json")
        if settings_path.exists():
            settings = {}
            try:
                settings = json.loads(settings_path.read_text(encoding="utf-8"))
            except ValueError:
                settings = {}
            def merge_setting(key, value):
                original = settings.get(key, None)
                if original is None or not str(original):
                    settings[key] = value
            merge_setting("python.venvPath", "/workspace")
            merge_setting("python.pythonPath",  "/workspace/.venv/bin/python")
            merge_setting("python.defaultInterpreterPath",  "/workspace/.venv/bin/python")
            merge_setting("claudeCode.preferredLocation",  "sidebar")
            merge_setting("claudeCode.allowDangerouslySkipPermissions", True)
            merge_setting("markdown-preview-enhanced.enablePreviewZenMode",  True)
            merge_setting("markdown-preview-enhanced.chromePath",  "/usr/bin/google-chrome-stable")
            settings_path.write_text(
                json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

    @classmethod
    def _parse_extension_dir(cls, name: str):
        match = re.match(r"^(.+)-(\d+(?:[.\-+][0-9A-Za-z]+)*)$", name)
        if not match:
            return None
        return match.group(1), match.group(2)

    @classmethod
    def _extension_version_key(cls, version: str):
        key = []
        for part in re.split(r"([0-9]+)", version):
            if not part:
                continue
            if part.isdigit():
                key.append((1, int(part)))
            else:
                key.append((0, part))
        return key

    @subcommand("clean", help="clean old code-server extensions")
    def on_exec_clean(self):
        extensions_path = self.get_app_path("home/.local/share/code-server/extensions")
        if not extensions_path.exists():
            self.logger.warning(f"Extensions path not found: {extensions_path}")
            return

        extensions = {}
        for path in extensions_path.iterdir():
            if not path.is_dir():
                continue
            parsed = self._parse_extension_dir(path.name)
            if not parsed:
                continue
            extension_name, version = parsed
            extensions.setdefault(extension_name, []).append((version, path))

        removed = 0
        for extension_name, versions in extensions.items():
            if len(versions) <= 1:
                continue
            versions.sort(key=lambda item: self._extension_version_key(item[0]))
            latest_version, latest_path = versions[-1]
            self.logger.info(f"Keep {extension_name} {latest_version}: {latest_path.name}")
            for version, path in versions[:-1]:
                self.logger.info(f"Remove {extension_name} {version}: {path.name}")
                shutil.rmtree(path)
                removed += 1

        self.logger.info(f"Cleaned {removed} old code-server extension(s)")
