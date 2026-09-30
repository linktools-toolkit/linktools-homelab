#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import secrets
from typing import Any, Iterable

from linktools.cli import subcommand
from linktools.cntr import BaseContainer, ExposeLink
from linktools.core import ConfigField, LazyProvider, PromptProvider
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            MCP_PUSH_TAG="latest",
            MCP_PUSH_DOMAIN=self.get_nginx_domain(),
            MCP_PUSH_PORT=ConfigField(cast=int, default=0),
            MCP_PUSH_TOKEN=ConfigField(secret=True, provider=LazyProvider(
                lambda r: secrets.token_hex(32), cached=True,
            )),
        )

    @cached_property
    def extend_configs(self) -> "dict[str, Any]":
        return {
            key: ConfigField.chain(
                PromptProvider(cached=True, allow_empty=True), name=key, secret=True,
            )
            for key in self.env_config.keys()
            if key.startswith("MCP_PUSH_") and key not in self.configs
        }

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("Push MCP", "bell", "多渠道消息推送 MCP（Bearer Token 认证）", self.load_nginx_url(
                "MCP_PUSH_DOMAIN", "mcp",
                proxy_conf=self.get_source_path("nginx.conf"),
                auth_enable=False,
                waf_enable=False,
            )),
            self.expose_container("Push MCP", "bell", "多渠道消息推送 MCP", self.load_port_url(
                "MCP_PUSH_PORT", "mcp", https=False,
            )),
        ]

    @subcommand("token", help="print the Bearer token for the push MCP endpoint")
    def on_exec_token(self):
        print(self.get_config("MCP_PUSH_TOKEN"))
