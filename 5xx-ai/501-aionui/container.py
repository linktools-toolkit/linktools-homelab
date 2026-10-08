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
from linktools.cntr import BaseContainer, ExposeLink, NginxSite


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx", "coder", "ai"]

    @cached_property
    def configs(self):
        return dict(
            AIONUI_TAG="latest",
            AIONUI_DOMAIN=self.get_nginx_domain(),
            AIONUI_PORT=ConfigField(cast=int, default=0),
            AIONUI_JWT_SECRET=ConfigField(provider=LazyProvider(lambda r: secrets.token_hex(24), cached=True)),
            AIONUI_TOKEN=ConfigField(provider=LazyProvider(lambda r: self._make_jwt(r.get("AIONUI_JWT_SECRET")))),
        )

    @cached_property
    def integrations(self) -> "dict[str, dict[str, NginxSite]]":
        return {"nginx": {"web": NginxSite(
            server_name=self.get_config_later("AIONUI_DOMAIN"),
            proxy="http://aionui:3000",
            template=self.get_source_path("nginx.conf"),
            auth=None,
            auth_headers={"Authorization": lazy_load(lambda: "Bearer " + self.get_config("AIONUI_TOKEN"))},
            auth_bypass=(r"\.(css|js|webmanifest)$",),
        )}}

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("AionUI", "robot", "AI 助手 Web UI", self.load_nginx_url("web")),
            self.expose_container("AionUI", "robot", "AI 助手 Web UI", self.load_port_url(
                "AIONUI_PORT",
                https=False,
            )),
        ]

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
