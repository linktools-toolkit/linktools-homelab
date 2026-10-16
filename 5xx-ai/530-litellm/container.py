#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import secrets
from typing import AbstractSet, Iterable, Mapping

from linktools.cli import subcommand
from linktools.core import ConfigField, LazyProvider, ConfigRef
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, Integrations
from linktools.cntr.ext import ResolvedSite, Nginx, endpoint, Flare, Authelia, load_nginx_url, load_port_url


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def oidc_provider(self) -> "BaseContainer | None":
        if "authelia" not in self.manager.integration_snapshot:
            return None
        provider = self.manager.containers["authelia"]
        if not provider.public_url.startswith("https://"):
            return None
        callback = self.env_config.resolve(load_nginx_url(ResolvedSite.find(self), "sso/callback"))
        redirects = provider.oidc_redirects
        return provider if provider.public_url in redirects and callback in redirects else None

    def get_runtime_requirements(self, required: AbstractSet[str]) -> Mapping[str, Iterable[str]]:
        if self.name in required and self.oidc_provider is not None:
            return {"authelia": ("authelia",)}
        return {}

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
        return endpoint(
            self,
            domain=ConfigRef("LITELLM_DOMAIN"),
            proxy="http://litellm:4000",
            auth=None,
            auth_bypass=(
                "^/v1/",
                "^/chat/completions",
                "^/completions",
                "^/embeddings",
                "^/health",
            ),
            extensions=[
                Flare.links(
                    Flare.public(
                        url="{base_url}/ui",
                    ),
                    Flare.container(
                        url=load_port_url(ConfigRef("LITELLM_PORT", type=int, default=0), "ui", https=False),
                    ),
                    name="LiteLLM",
                    icon="api",
                    desc="LiteLLM Proxy & Web UI",
                ),
                Authelia.oidc(
                    redirect_uris=("{base_url}/sso/callback",),
                ),
            ],
        )

    @subcommand("key", help="print the master key for Web UI login")
    def on_exec_key(self):
        print(self.get_config("LITELLM_MASTER_KEY"))
