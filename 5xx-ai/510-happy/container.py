#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Iterable

from linktools.core import ConfigField, PromptProvider
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, ExposeLink


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            HAPPY_TAG="latest",
            HAPPY_SERVER_DOMAIN=self.get_nginx_domain(),
            HAPPY_SERVER_PORT=ConfigField(cast=int, default=0),
            HAPPY_SECRET=ConfigField(provider=PromptProvider(cached=True)),
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("Happy", "cellphoneLink", "Claude Code 移动端中继服务", self.load_nginx_url(
                "HAPPY_SERVER_DOMAIN",
                proxy_url="http://happy-server:3000",
                auth_enable=True,
            )),
            self.expose_container("Happy", "cellphoneLink", "Claude Code 移动端中继服务", self.load_port_url(
                "HAPPY_SERVER_PORT",
                https=False,
            )),
        ]
