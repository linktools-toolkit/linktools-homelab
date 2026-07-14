#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import os
import random
import string
from typing import Iterable

from linktools.core import ConfigField, LazyProvider
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, ExposeLink, EventContext


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx", "ai"]

    @cached_property
    def configs(self):
        return dict(
            CC_SWITCH_TAG="latest",
            CC_SWITCH_DOMAIN=self.get_nginx_domain(),
            CC_SWITCH_PORT=ConfigField(cast=int, default=0),
            CC_SWITCH_PASSWORD=ConfigField(provider=LazyProvider(
                lambda r: "".join(random.sample(string.ascii_letters + string.digits, 16)), cached=True,
            )),
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("CC Switch", "tune", "AI CLI 配置管理面板", self.load_nginx_url(
                "CC_SWITCH_DOMAIN",
                proxy_url="http://cc-switch-web:3000",
                auth_enable=True,
                auth_extra={
                    "auth_headers": {
                        "Authorization": "Basic " + base64.b64encode(
                            f"admin:{self.get_config('CC_SWITCH_PASSWORD')}".encode()
                        ).decode(),
                    },
                },
            )),
            self.expose_container("CC Switch", "tune", "AI CLI 配置管理面板", self.load_port_url(
                "CC_SWITCH_PORT",
                https=False,
            )),
        ]

    def on_starting(self, context: "EventContext"):
        password_file = os.path.join(self.get_app_path("data"), "web_password")
        os.makedirs(os.path.dirname(password_file), mode=0o755, exist_ok=True)
        with open(password_file, "w") as f:
            f.write(self.get_config("CC_SWITCH_PASSWORD"))
