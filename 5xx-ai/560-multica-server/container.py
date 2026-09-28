#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import secrets
from typing import Iterable

from linktools.core import ConfigField, LazyProvider
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, ExposeLink


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            MULTICA_TAG="latest",
            MULTICA_DOMAIN=self.get_nginx_domain("multica"),
            MULTICA_FRONTEND_PORT=ConfigField(cast=int, default=0),
            MULTICA_BACKEND_PORT=ConfigField(cast=int, default=0),
            MULTICA_JWT_SECRET=ConfigField(provider=LazyProvider(lambda r: secrets.token_hex(32), cached=True)),
            MULTICA_DB_PASSWORD=ConfigField(provider=LazyProvider(lambda r: secrets.token_hex(24), cached=True)),
            MULTICA_VCS_SECRET_KEY=ConfigField(provider=LazyProvider(
                lambda r: base64.b64encode(secrets.token_bytes(32)).decode(), cached=True,
            )),
            MULTICA_ALLOW_SIGNUP=ConfigField(cast=bool, default=True),
            MULTICA_ALLOWED_EMAILS="",
            MULTICA_ALLOWED_EMAIL_DOMAINS="",
            MULTICA_RESEND_API_KEY="",
            MULTICA_RESEND_FROM_EMAIL="noreply@multica.ai",
            MULTICA_GOOGLE_CLIENT_ID="",
            MULTICA_GOOGLE_CLIENT_SECRET="",
            MULTICA_SMTP_HOST="",
            MULTICA_SMTP_PORT="25",
            MULTICA_SMTP_USERNAME="",
            MULTICA_SMTP_PASSWORD="",
            MULTICA_SMTP_FROM_EMAIL="",
            MULTICA_SMTP_TLS="starttls",
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("Multica", "robot", "AI Agent Team Platform", self.load_nginx_url(
                "MULTICA_DOMAIN",
                proxy_conf=self.get_source_path("nginx.conf"),
                auth_enable=True,
                waf_enable=False,
            )),
            self.expose_container("Multica", "robot", "AI Agent Team Platform", self.load_port_url(
                "MULTICA_FRONTEND_PORT", https=False,
            )),
            self.expose_container("Multica API", "robot", "AI Agent Team API", self.load_port_url(
                "MULTICA_BACKEND_PORT", https=False,
            )),
        ]
