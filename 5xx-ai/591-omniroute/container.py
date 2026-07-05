#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import secrets
from typing import Iterable

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
            OMNIROUTE_TAG="latest",
            OMNIROUTE_DOMAIN=self.get_nginx_domain(),
            OMNIROUTE_PORT=Config.Alias(type=int, default=0),
            # Require an API key on all requests (recommended when exposed publicly)
            OMNIROUTE_REQUIRE_API_KEY=Config.Alias(type=bool, default=True),
            # Fixed secrets — framework-managed so they survive rebuilds/rehosts.
            # OmniRoute auto-generates these in DATA_DIR/server.env on first launch;
            # setting them via env lets the framework own & persist them in config.
            OMNIROUTE_JWT_SECRET=Config.Alias(cached=True) | secrets.token_hex(32),
            OMNIROUTE_STORAGE_KEY=Config.Alias(cached=True) | secrets.token_hex(32),
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("OmniRoute", "transitConnectionVariant", "Free self-hosted AI gateway", self.load_nginx_url(
                "OMNIROUTE_DOMAIN",
                proxy_url="http://omniroute:20128",
                auth_enable=True,
                auth_extra={
                    # The /v1, /vscode, /api/mcp and relay endpoints are meant to be
                    # consumed by coding tools with their own API key, so they bypass
                    # the Authelia SSO that protects the dashboard.
                    "acl_bypass": [
                        "^/v1/",
                        "^/vscode/",
                        "^/v1/relay",
                        "^/api/mcp/",
                    ],
                },
            )),
            self.expose_container("OmniRoute", "transitConnectionVariant", "Free self-hosted AI gateway", self.load_port_url(
                "OMNIROUTE_PORT", https=False,
            )),
        ]
