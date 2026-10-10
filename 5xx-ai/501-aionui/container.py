#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Iterable

from linktools.core import ConfigField, LazyProvider
from linktools.decorator import cached_property
from linktools.runtime import lazy_load
from linktools.cntr import BaseContainer, Integrations
from linktools.cntr.ext import Nginx, Flare, load_port_url


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx", "coder", "ai"]

    @cached_property
    def configs(self):
        return dict(
            AIONUI_TAG="latest",
            AIONUI_DOMAIN=Nginx.domain(self),
            AIONUI_PORT=ConfigField(cast=int, default=0),
            AIONUI_JWT_SECRET=ConfigField(provider=LazyProvider(lambda r: secrets.token_hex(24), cached=True)),
            AIONUI_TOKEN=ConfigField(provider=LazyProvider(lambda r: self._make_jwt(r.get("AIONUI_JWT_SECRET")))),
        )

    @cached_property
    def integrations(self) -> Integrations:
        return (
            Nginx.site(
                link=Flare.public("AionUI", "robot", "AI 助手 Web UI"),
                server_name=self.get_config_later("AIONUI_DOMAIN"),
                proxy="http://aionui:3000",
                template=self.get_source_path("nginx.conf"),
                auth=None,
                auth_headers={"Authorization": lazy_load(lambda: "Bearer " + self.get_config("AIONUI_TOKEN"))},
                auth_bypass=(r"\.(css|js|webmanifest)$",),
            ),
            Flare.container("AionUI", "robot", load_port_url(
                self, "AIONUI_PORT",
                https=False,
            ), desc="AI 助手 Web UI"),
        )

    @classmethod
    def _make_jwt(cls, secret: str) -> str:
        def b64url(obj):
            data = json.dumps(obj, separators=(",", ":")).encode() if isinstance(obj, dict) else obj
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

        now = int(time.time())
        header = b64url({"alg": "HS256", "typ": "JWT"})
        payload = b64url({
            "user_id": "system_default_user",
            "username": "system_default_user",
            "iat": now,
            "exp": now + 100 * 365 * 24 * 3600,  # 100 years
            "iss": "aionui",
            "aud": "aionui-webui",
        })
        sig = base64.urlsafe_b64encode(
            hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
        ).rstrip(b"=").decode()
        return f"{header}.{payload}.{sig}"
