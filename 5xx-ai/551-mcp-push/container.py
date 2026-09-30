#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import secrets
from typing import Any, Iterable

from linktools.cli import subcommand, subcommand_argument
from linktools.cntr import BaseContainer, ExposeLink
from linktools.core import ConfigField, LazyProvider, PromptProvider
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
                PromptProvider(cached=True, allow_empty=True), name=key,
                secret=key != "MCP_PUSH_ALLOWED_ORIGINS",
            )
            for key in self.env_config.keys()
            if key in PUSH_RUNTIME_CONFIGS and key not in self.configs
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
                    "url": str(self.load_exist_nginx_url("MCP_PUSH_DOMAIN", "mcp")),
                    "headers": headers,
                },
            },
        }
        print(json.dumps(config, indent=2, ensure_ascii=False))
