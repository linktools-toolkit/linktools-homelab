#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import secrets
from typing import Iterable

from linktools.core import ConfigField, LazyProvider
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
            OMNIROUTE_PORT=ConfigField(cast=int, default=0),
            OMNIROUTE_REQUIRE_API_KEY=ConfigField(cast=bool, default=True),
            OMNIROUTE_JWT_SECRET=ConfigField(provider=LazyProvider(lambda r: secrets.token_hex(32), cached=True)),
            OMNIROUTE_STORAGE_KEY=ConfigField(provider=LazyProvider(lambda r: secrets.token_hex(32), cached=True)),
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("OmniRoute", "transitConnectionVariant", "Free self-hosted AI gateway", self.load_nginx_url(
                "OMNIROUTE_DOMAIN",
                proxy_url="http://omniroute:20128",
                auth_enable=True,
                auth_extra={
                    "acl_bypass": [
                        "^/(v1|vscode|api/mcp)(/|$)",
                    ],
                },
            )),
            self.expose_container("OmniRoute", "transitConnectionVariant", "Free self-hosted AI gateway", self.load_port_url(
                "OMNIROUTE_PORT", https=False,
            )),
        ]
