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
from linktools.cntr import BaseContainer, EventContext, ExposeLink


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
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("AionUI", "robot", "AI 助手 Web UI", self.load_nginx_url(
                "AIONUI_DOMAIN",
                proxy_url="http://aionui:3000",
                auth_enable=True,
                auth_extra={
                    "auth_headers": {
                        "Authorization": f"Bearer {self.get_config('AIONUI_TOKEN')}"
                    },
                    "acl_bypass": ["\\.(css|js|webmanifest)$"],
                },
            )),
            self.expose_container("AionUI", "robot", "AI 助手 Web UI", self.load_port_url(
                "AIONUI_PORT",
                https=False,
            )),
        ]

    def on_starting(self, context: "EventContext"):
        self.write_nginx_conf(
            self.get_config("AIONUI_DOMAIN"),
            proxy_name="logout",
            proxy_conf=self.get_source_path("nginx.conf"),
            auth_enable=True
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
