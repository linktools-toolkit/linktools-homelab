#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import secrets
from typing import Iterable

from linktools.core import ConfigField, LazyProvider
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, Integrations
from linktools.cntr.ext import Nginx, endpoint, Flare, load_port_url


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            OMNIROUTE_TAG="latest",
            OMNIROUTE_DOMAIN=Nginx.domain(self),
            OMNIROUTE_PORT=ConfigField(cast=int, default=0),
            OMNIROUTE_REQUIRE_API_KEY=ConfigField(cast=bool, default=True),
            OMNIROUTE_JWT_SECRET=ConfigField(provider=LazyProvider(lambda r: secrets.token_hex(32), cached=True)),
            OMNIROUTE_STORAGE_KEY=ConfigField(provider=LazyProvider(lambda r: secrets.token_hex(32), cached=True)),
        )

    @cached_property
    def integrations(self) -> Integrations:
        return endpoint(
            self,
            domain=self.get_config_later("OMNIROUTE_DOMAIN"),
            proxy="http://omniroute:20128",
            template_vars={"client_max_body_size": "10m"},
            auth_bypass=(r"^/(v1|vscode|api/mcp)(/|$)", r"\.(css|js|webmanifest)$"),
            waf_bypass=(r"^/(v1|vscode|api/mcp)(/|$)",),
            extensions=[
                Flare.links(
                    Flare.public(),
                    Flare.container(
                        url=load_port_url(self, "OMNIROUTE_PORT", https=False),
                    ),
                    name="OmniRoute",
                    icon="transitConnectionVariant",
                    desc="Free self-hosted AI gateway",
                ),
            ],
        )
