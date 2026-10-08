#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import secrets
from typing import Any, Iterable

from linktools.core import ConfigField, LazyProvider, PromptProvider
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, Integrations, NginxSite


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
            MULTICA_LARK_SECRET_KEY=ConfigField(secret=True, provider=LazyProvider(
                lambda r: base64.b64encode(secrets.token_bytes(32)).decode(), cached=True,
            )),
            MULTICA_SLACK_SECRET_KEY=ConfigField(secret=True, provider=LazyProvider(
                lambda r: base64.b64encode(secrets.token_bytes(32)).decode(), cached=True,
            )),
            MULTICA_DINGTALK_SECRET_KEY=ConfigField(secret=True, provider=LazyProvider(
                lambda r: base64.b64encode(secrets.token_bytes(32)).decode(), cached=True,
            )),
            MULTICA_WECOM_SECRET_KEY=ConfigField(secret=True, provider=LazyProvider(
                lambda r: base64.b64encode(secrets.token_bytes(32)).decode(), cached=True,
            )),
            MULTICA_TELEGRAM_SECRET_KEY=ConfigField(secret=True, provider=LazyProvider(
                lambda r: base64.b64encode(secrets.token_bytes(32)).decode(), cached=True,
            )),
            MULTICA_ALLOW_SIGNUP=ConfigField(cast=bool, default=True),
            MULTICA_ALLOWED_EMAILS="",
            MULTICA_ALLOWED_EMAIL_DOMAINS="",
            MULTICA_RESEND_API_KEY="",
            MULTICA_RESEND_FROM_EMAIL="noreply@multica.ai",
            MULTICA_GOOGLE_CLIENT_ID="",
            MULTICA_GOOGLE_CLIENT_SECRET="",
            MULTICA_GITHUB_APP_SLUG="",
            MULTICA_GITHUB_WEBHOOK_SECRET=ConfigField(secret=True, provider=LazyProvider(
                lambda r: secrets.token_hex(32), cached=True,
            )),
            MULTICA_GITHUB_APP_ID="",
            MULTICA_GITHUB_APP_PRIVATE_KEY=ConfigField(default="", secret=True),
            MULTICA_SMTP_HOST="",
            MULTICA_SMTP_PORT="25",
            MULTICA_SMTP_USERNAME="",
            MULTICA_SMTP_PASSWORD="",
            MULTICA_SMTP_FROM_EMAIL="",
            MULTICA_SMTP_TLS="starttls",
        )

    @cached_property
    def extend_configs(self) -> "dict[str, Any]":
        excluded = set(self.configs)
        multica = self.containers.get("multica")
        if multica is not None and multica.enable:
            excluded.update(multica.configs)

        configs = {}
        for key in self.env_config.keys():
            if not key.startswith("MULTICA_") or key in excluded:
                continue
            configs[key] = ConfigField.chain(
                PromptProvider(cached=True, allow_empty=True),
                name=key,
            )
        return configs

    @cached_property
    def integrations(self) -> Integrations:
        return {
            "nginx": {
                "web": NginxSite(
                    expose=self.expose_public("Multica", "robot", "AI Agent Team Platform"),
                    server_name=self.get_config_later("MULTICA_DOMAIN"),
                    template=self.get_source_path("nginx.conf"),
                    waf=False,
                    auth=None,
                ),
            },
            "flare": {
                "frontend_direct": self.expose_container("Multica", "robot", "AI Agent Team Platform", self.load_port_url(
                    "MULTICA_FRONTEND_PORT", https=False,
                )),
                "api_direct": self.expose_container("Multica API", "robot", "AI Agent Team API", self.load_port_url(
                    "MULTICA_BACKEND_PORT", https=False,
                )),
            },
        }
