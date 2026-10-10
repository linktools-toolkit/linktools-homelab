#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import secrets
from typing import Iterable

from linktools.cli import subcommand
from linktools.core import ConfigField, LazyProvider
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, Integrations
from linktools.cntr.ext import Authelia, Nginx, Flare, load_nginx_url, load_port_url


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            LITELLM_TAG="main-latest",
            LITELLM_DOMAIN=Nginx.domain(self),
            LITELLM_PORT=ConfigField(cast=int, default=0),
            LITELLM_MASTER_KEY=ConfigField(provider=LazyProvider(
                lambda r: f"sk-{secrets.token_hex(24)}", cached=True,
            )),
            LITELLM_SALT_KEY=ConfigField(provider=LazyProvider(lambda r: secrets.token_hex(32), cached=True)),
            LITELLM_DB_HOST="litellm-postgres",
            LITELLM_DB_PORT="5432",
            LITELLM_DB_DATABASE="litellm",
            LITELLM_DB_USERNAME="litellm",
            LITELLM_DB_PASSWORD=ConfigField(provider=LazyProvider(lambda r: secrets.token_hex(16), cached=True)),
        )

    @cached_property
    def integrations(self) -> Integrations:
        return (
            Nginx.site(
                server_name=self.get_config_later("LITELLM_DOMAIN"),
                proxy="http://litellm:4000",
                auth=None,
                auth_bypass=("^/v1/", "^/chat/completions", "^/completions", "^/embeddings", "^/health",),
            ),
            Flare.public("LiteLLM", "api", "LiteLLM Proxy & Web UI", load_nginx_url(self, "web", "ui")),
            Flare.container("LiteLLM", "api", load_port_url(
                self, "LITELLM_PORT", "ui",
                https=False,
            ), desc="LiteLLM Proxy & Web UI"),
            Authelia.oidc(
                redirect_uris=(load_nginx_url(self, "web", "sso/callback"),),
                enabled=self.get_config_later("NGINX_AUTH_ENABLE"),
            ),
        )

    @subcommand("key", help="print the master key for Web UI login")
    def on_exec_key(self):
        print(self.get_config("LITELLM_MASTER_KEY"))
