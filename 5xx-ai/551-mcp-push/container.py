#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import secrets
from typing import Any, Iterable

from linktools.cli import subcommand, subcommand_argument
from linktools.cntr import BaseContainer, Integrations
from linktools.cntr.ext import ResolvedSite, Nginx, load_nginx_url, endpoint
from linktools.core import ConfigField, LazyProvider, PromptProvider, ConfigRef
from linktools.decorator import cached_property


PUSH_CHANNEL_HEADERS = {
    "ServerChanV3": ("SERVER_CHAN_V3_SENDKEY",),
    "CustomEmail": ("EMAIL_TO_ADDRESS", "EMAIL_AUTH_USER", "EMAIL_AUTH_PASS", "EMAIL_HOST"),
    "Dingtalk": ("DINGTALK_ACCESS_TOKEN", "DINGTALK_SECRET"),
    "WechatApp": ("WECHAT_APP_CORPID", "WECHAT_APP_SECRET", "WECHAT_APP_AGENTID"),
    "Feishu": ("FEISHU_APP_ID", "FEISHU_APP_SECRET"),
    "Discord": ("DISCORD_WEBHOOK",),
    "Telegram": ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"),
    "Ntfy": ("NTFY_URL", "NTFY_TOPIC"),
}
PUSH_RUNTIME_CONFIGS = {
    "MCP_PUSH_ALLOWED_ORIGINS",
    "MCP_PUSH_HTTP_PROXY",
    "MCP_PUSH_HTTPS_PROXY",
    "MCP_PUSH_SOCKS_PROXY",
    "MCP_PUSH_NO_PROXY",
}


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def fields(self):
        return dict(
            MCP_PUSH_TAG="latest",
            MCP_PUSH_DOMAIN=Nginx.domain(self),
            MCP_PUSH_PORT=ConfigField(cast=int, default=0),
            MCP_PUSH_TOKEN=ConfigField(secret=True, provider=LazyProvider(
                lambda r: secrets.token_hex(32), cached=True,
            )),
        )

    @cached_property
    def extra_fields(self) -> "dict[str, Any]":
        return {
            key: ConfigField.chain(
                PromptProvider(cached=True, allow_empty=True), name=key,
                secret=key != "MCP_PUSH_ALLOWED_ORIGINS",
            )
            for key in self.config.keys()
            if key in PUSH_RUNTIME_CONFIGS and key not in self.fields
        }

    @cached_property
    def integrations(self) -> Integrations:
        return endpoint(
            self,
            domain=ConfigRef("MCP_PUSH_DOMAIN"),
            template=self.get_source_path("nginx.conf"),
            waf=False,
            auth=False,
            extensions=[],
        )

    @subcommand("show", help="print MCP server JSON configuration, optionally with a channel example")
    @subcommand_argument("channel", nargs="?", choices=tuple(PUSH_CHANNEL_HEADERS),
                         help="push channel, for example Feishu")
    def on_exec_show(self, channel: "str | None" = None):
        headers = {
            "Authorization": f"Bearer {self.get_config('MCP_PUSH_TOKEN')}",
        }
        if channel:
            headers["X-CHANNEL"] = channel
            headers.update({
                f"X-{key.replace('_', '-')}": f"<{key}>"
                for key in PUSH_CHANNEL_HEADERS[channel]
            })
        config = {
            "mcpServers": {
                "push": {
                    "url": self.config.resolve(load_nginx_url(ResolvedSite.find(self), "mcp")),
                    "headers": headers,
                },
            },
        }
        print(json.dumps(config, indent=2, ensure_ascii=False))
