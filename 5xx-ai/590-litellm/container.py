#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import secrets
from typing import Iterable

from linktools.cli import subcommand
from linktools.core import Config
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, ExposeLink


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            LITELLM_TAG="main-latest",
            LITELLM_DOMAIN=self.get_nginx_domain(),
            LITELLM_PORT=Config.Alias(type=int, default=0),
            LITELLM_MASTER_KEY=Config.Alias(cached=True) | f"sk-{secrets.token_hex(24)}",
            LITELLM_SALT_KEY=Config.Alias(cached=True) | secrets.token_hex(32),
            LITELLM_DB_HOST="litellm-postgres",
            LITELLM_DB_PORT="5432",
            LITELLM_DB_DATABASE="litellm",
            LITELLM_DB_USERNAME="litellm",
            LITELLM_DB_PASSWORD=Config.Alias(cached=True) | secrets.token_hex(16),
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("LiteLLM", "api", "LiteLLM Proxy & Web UI", self.load_nginx_url(
                "LITELLM_DOMAIN", "ui",
                proxy_url="http://litellm:4000",
                auth_enable=True,
                auth_extra={
                    "oidc_redirect_uris": ["{base_url}/sso/callback"],
                    "acl_bypass": [
                        "^/v1/",
                        "^/chat/completions",
                        "^/completions",
                        "^/embeddings",
                        "^/health",
                    ],
                },
            )),
            self.expose_container("LiteLLM", "api", "LiteLLM Proxy & Web UI", self.load_port_url(
                "LITELLM_PORT", "ui",
                https=False,
            )),
        ]

    @subcommand("key", help="print the master key for Web UI login")
    def on_exec_key(self):
        print(self.get_config("LITELLM_MASTER_KEY"))
