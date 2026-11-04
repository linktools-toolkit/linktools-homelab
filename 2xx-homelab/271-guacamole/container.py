#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Single-user web RDP/VNC access through Authelia-authenticated Guacamole."""
import secrets
from typing import Iterable

from linktools.cntr import BaseContainer, Integrations, OperationContext
from linktools.cntr.ext import Flare, Nginx, endpoint
from linktools.core import ConfigField, ConfigRef, LazyProvider
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ("nginx", "authelia")

    @cached_property
    def fields(self):
        return dict(
            GUACAMOLE_TAG="1.6.0",
            GUACAMOLE_DOMAIN=Nginx.domain(self),
            GUACAMOLE_DB_PASSWORD=ConfigField(provider=LazyProvider(
                lambda r: secrets.token_urlsafe(32), cached=True,
            )),
        )

    @cached_property
    def integrations(self) -> Integrations:
        return endpoint(
            self,
            domain=ConfigRef("GUACAMOLE_DOMAIN"),
            proxy="http://guacamole:8080",
            https=True,
            auth=True,
            auth_headers={"REMOTE_USER": "guacadmin"},
            extensions=[
                Flare.public("Guacamole", "remoteDesktop", "Web 远程桌面（RDP/VNC）"),
            ],
        )

    def on_started(self, context: OperationContext) -> None:
        self.manager.runtime.create_docker_process(
            "exec",
            self.get_service_name("guacamole-postgres"),
            "psql",
            "-U", "guacamole",
            "-d", "guacamole",
            "-v", "ON_ERROR_STOP=1",
            "-f", "/docker-entrypoint-initdb.d/002-create-admin-user.sql",
        ).check_call()
