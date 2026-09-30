#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Iterable

from linktools.cntr import BaseContainer, ExposeLink
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
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("CloudCLI", "messageOutline", "Cloud CLI", self.load_nginx_url(
                "CLOUD_CLI_DOMAIN",
                proxy_url="http://cloudcli:3001",
                auth_enable=True,
                auth_extra={
                    "acl_bypass": ["\\.(css|js)$"],
                }
            )),
            self.expose_container("CloudCLI", "messageOutline", "Cloud CLI", self.load_port_url(
                "CLOUD_CLI_PORT",
                https=False
            )),
        ]
