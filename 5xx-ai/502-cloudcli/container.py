#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Iterable

from linktools.cntr import BaseContainer, Integrations
from linktools.cntr.ext import Nginx, endpoint, Flare, load_port_url
from linktools.core import ConfigField, ConfigRef
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx", "coder", "ai"]

    @cached_property
    def fields(self):
        return dict(
            CLOUD_CLI_TAG="latest",
            CLOUD_CLI_DOMAIN=Nginx.domain(self),
            CLOUD_CLI_PORT=ConfigField(cast=int, default=0),
        )

    @cached_property
    def integrations(self) -> Integrations:
        return endpoint(
            self,
            domain=ConfigRef("CLOUD_CLI_DOMAIN"),
            proxy="http://cloudcli:3001",
            auth_bypass=(r"\.(css|js)$",),
            extensions=[
                Flare.links(
                    Flare.public(),
                    Flare.container(
                        url=load_port_url(ConfigRef("CLOUD_CLI_PORT"), https=False),
                    ),
                    name="CloudCLI",
                    icon="messageOutline",
                    desc="Cloud CLI",
                ),
            ],
        )
