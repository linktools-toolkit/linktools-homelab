#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Iterable

from linktools.cntr import BaseContainer, Integrations, NginxSite, ExposeLink
from linktools.cntr.urls import load_port_url
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
            CLOUD_CLI_DOMAIN=self.get_nginx_domain(),
            CLOUD_CLI_PORT=ConfigField(cast=int, default=0),
        )

    @cached_property
    def integrations(self) -> Integrations:
        return {
            "nginx": {
                "web": NginxSite(
                    expose=ExposeLink.public("CloudCLI", "messageOutline", "Cloud CLI"),
                    server_name=self.get_config_later("CLOUD_CLI_DOMAIN"),
                    proxy="http://cloudcli:3001",
                    auth_bypass=(r"\.(css|js)$",),
                ),
            },
            "flare": [
                ExposeLink.container("CloudCLI", "messageOutline", "Cloud CLI", load_port_url(
                    self, "CLOUD_CLI_PORT",
                    https=False
                )),
            ],
        }
