#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Iterable

from linktools import utils
from linktools.cli import subcommand, subcommand_argument
from linktools.core import ConfigField
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, ExposeLink


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            HERMES_AGENT_TAG="latest",
            HERMES_AGENT_DOMAIN=self.get_nginx_domain(),
            HERMES_AGENT_PORT=ConfigField(cast=int, default=0),
            HERMES_AGENT_DASHBOARD_PORT=ConfigField(cast=int, default=0),
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("Hermes Agent", "robot", "AI Agent Dashboard", self.load_nginx_url(
                "HERMES_AGENT_DOMAIN",
                proxy_url="http://hermes-dashboard:9120",
                proxy_conf=self.get_source_path("nginx.conf"),
                auth_enable=True,
                waf_enable=False,
            )),
            self.expose_container("Hermes API", "robot", "AI Agent Gateway API", self.load_port_url(
                "HERMES_AGENT_PORT",
                https=False,
            )),
            self.expose_container("Hermes Dashboard", "robot", "AI Agent Dashboard", self.load_port_url(
                "HERMES_AGENT_DASHBOARD_PORT",
                https=False,
            )),
        ]

    @subcommand("cli", help="run hermes CLI command", prefix_chars=chr(1))
    @subcommand_argument("args", nargs="...", metavar="ARGS", help="hermes args")
    def on_exec(self, args: "list[str]"):
        self.manager.runtime.create_docker_process(
            "exec", "-it", self.get_service_name("hermes"),
            "sh", "-c", utils.list2cmdline(['.venv/bin/hermes', *args]),
        ).check_call()
