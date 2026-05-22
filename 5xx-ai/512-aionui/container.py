#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import hashlib
import hmac
import json
import secrets
import uuid
from typing import Iterable

from linktools.core import Config
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, ExposeLink


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx", "coder", "ai"]

    @cached_property
    def configs(self):
        return dict(
            AIONUI_TAG="latest",
            AIONUI_DOMAIN=self.get_nginx_domain(),
            AIONUI_PORT=Config.Alias(type=int) | 0,
            AIONUI_JWT_SECRET=Config.Alias(cached=True) | secrets.token_hex(24),
            AIONUI_TOKEN=Config.Lazy(lambda cfg: self._make_jwt(cfg.get("AIONUI_JWT_SECRET"))),
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
                },
            )),
            self.expose_container("AionUI", "robot", "AI 助手 Web UI", self.load_port_url(
                "AIONUI_PORT",
                https=False,
            )),
        ]

    def on_prepare(self):
        coder = self.manager.containers["coder"]
        coder.install_modules[self.get_service_name("aionui")] = [
            {"type": "shell", "module": "curl -fsSL https://claude.ai/install.sh | bash"},
            {"type": "npm", "module": "@openai/codex@latest"},
            {"type": "npm", "module": "@google/gemini-cli@latest"},
            {"type": "npm", "module": "npx@latest"},
        ]

    @classmethod
    def _make_jwt(cls, secret: str) -> str:
        def b64url(obj):
            data = json.dumps(obj, separators=(",", ":")).encode() if isinstance(obj, dict) else obj
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

        header = b64url({"alg": "HS256", "typ": "JWT"})
        payload = b64url({
            "userId": "system_default_user",
            "username": "system_default_user",
            "tokenId": str(uuid.uuid4()),
            "iss": "aionui",
            "aud": "aionui-webui",
        })
        sig = base64.urlsafe_b64encode(
            hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
        ).rstrip(b"=").decode()
        return f"{header}.{payload}.{sig}"
