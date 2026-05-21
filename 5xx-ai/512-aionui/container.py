#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
            AIONUI_TAG="latest",
            AIONUI_DOMAIN=self.get_nginx_domain(),
            AIONUI_PORT=Config.Alias(type=int, default=0),
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("AionUI", "robot", "AI 助手 Web UI", self.load_nginx_url(
                "AIONUI_DOMAIN",
                proxy_url="http://aionui:3000",
                auth_enable=True,
            )),
            self.expose_container("AionUI", "robot", "AI 助手 Web UI", self.load_port_url(
                "AIONUI_PORT",
                https=False,
            )),
        ]
