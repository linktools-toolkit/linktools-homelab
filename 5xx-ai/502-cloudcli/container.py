#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Iterable

from linktools.cntr import BaseContainer, Integrations
from linktools.cntr.ext import Nginx, Flare, load_port_url
from linktools.core import ConfigField
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx", "coder", "ai"]

    @cached_property
    def configs(self):
        return dict(
            CLOUD_CLI_TAG="latest",
            CLOUD_CLI_DOMAIN=Nginx.domain(self),
            CLOUD_CLI_PORT=ConfigField(cast=int, default=0),
        )

    @cached_property
    def integrations(self) -> Integrations:
        return (
            Nginx.site(
                link=Flare.public("CloudCLI", "messageOutline", "Cloud CLI"),
                server_name=self.get_config_later("CLOUD_CLI_DOMAIN"),
                proxy="http://cloudcli:3001",
                auth_bypass=(r"\.(css|js)$",),
            ),
            Flare.container("CloudCLI", "messageOutline", load_port_url(
                self, "CLOUD_CLI_PORT",
                https=False
            ), desc="Cloud CLI"),
        )
