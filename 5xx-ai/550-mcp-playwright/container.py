#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import secrets
from typing import Iterable

from linktools.cli import subcommand
from linktools.cntr import BaseContainer, Integrations
from linktools.cntr.ext import Nginx, Flare, load_nginx_url, load_port_url
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
            MCP_PLAYWRIGHT_DOMAIN=Nginx.domain(self),
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
    def integrations(self) -> Integrations:
        return (
            Nginx.site(
                link=Flare.public("Playwright Browser", "web", "通过 noVNC 操作 MCP 浏览器"),
                server_name=self.get_config_later("MCP_PLAYWRIGHT_DOMAIN"),
                template=self.get_source_path("nginx.conf"),
                waf=False,
                auth=None,
            ),
            Flare.container("Playwright Browser", "web", load_port_url(
                self, "MCP_PLAYWRIGHT_NOVNC_PORT", https=False,
            ), desc="noVNC 浏览器"),
        )

    @subcommand("show", help="print MCP server JSON configuration")
    def on_exec_show(self):
        config = {
            "mcpServers": {
                "playwright": {
                    "url": str(load_nginx_url(self, "web", "mcp")),
                    "headers": {
                        "Authorization": f"Bearer {self.get_config('MCP_PLAYWRIGHT_TOKEN')}",
                    },
                },
            },
        }
        print(json.dumps(config, indent=2, ensure_ascii=False))
