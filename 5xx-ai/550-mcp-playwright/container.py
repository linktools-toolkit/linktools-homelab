#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import secrets
from typing import Iterable

from linktools.cli import subcommand
from linktools.cntr import BaseContainer, ExposeLink
from linktools.core import ConfigField, LazyProvider
from linktools.decorator import cached_property


def validate_token(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", value):
        raise ValueError("MCP_PLAYWRIGHT_TOKEN must contain 32-128 letters, digits, underscores or hyphens")
    return value


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            MCP_PLAYWRIGHT_TAG="latest",
            MCP_PLAYWRIGHT_DOMAIN=self.get_nginx_domain(),
            MCP_PLAYWRIGHT_TOKEN=ConfigField(
                cast=validate_token,
                provider=LazyProvider(lambda r: secrets.token_hex(32), cached=True),
            ),
            MCP_PLAYWRIGHT_PORT=ConfigField(cast=int, default=0),
            MCP_PLAYWRIGHT_NOVNC_PORT=ConfigField(cast=int, default=0),
            MCP_PLAYWRIGHT_SCREEN_WIDTH=ConfigField(cast=int, default=1440),
            MCP_PLAYWRIGHT_SCREEN_HEIGHT=ConfigField(cast=int, default=900),
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("Playwright Browser", "web", "通过 noVNC 操作 MCP 浏览器", self.load_nginx_url(
                "MCP_PLAYWRIGHT_DOMAIN",
                proxy_conf=self.get_source_path("nginx.conf"),
                auth_enable=True,
                waf_enable=False,
            )),
            self.expose_public("Playwright MCP", "robot", "MCP HTTP 服务（Bearer Token 认证）", self.load_exist_nginx_url(
                "MCP_PLAYWRIGHT_DOMAIN", "mcp",
            )),
            self.expose_container("Playwright Browser", "web", "noVNC 浏览器", self.load_port_url(
                "MCP_PLAYWRIGHT_NOVNC_PORT", https=False,
            )),
            self.expose_container("Playwright MCP", "robot", "MCP HTTP 服务（路径 /mcp）", self.load_port_url(
                "MCP_PLAYWRIGHT_PORT", "mcp", https=False,
            )),
        ]

    @subcommand("token", help="print the Bearer token for the public MCP endpoint")
    def on_exec_token(self):
        print(self.get_config("MCP_PLAYWRIGHT_TOKEN"))
