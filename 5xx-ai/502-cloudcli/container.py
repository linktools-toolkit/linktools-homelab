#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import Iterable

from linktools.cntr import BaseContainer, ContainerError, Integrations
from linktools.cntr.lifecycle import HookPhase
from linktools.cntr.ext import Nginx, endpoint, Flare, load_port_url
from linktools.core import ConfigField, ConfigRef
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["vscode"]

    @cached_property
    def fields(self):
        return dict(
            CLOUD_CLI_DOMAIN=Nginx.domain(self),
            CLOUD_CLI_PORT=ConfigField(cast=int, default=0),
        )

    def on_init(self):
        # on_init runs after every container is constructed, so VSCode's hook
        # registry is reachable here. Register unconditionally: installed
        # state is only known when Compose is rendered (checked in the hook).
        vscode = self.containers.get("vscode")
        if vscode is not None:
            vscode.hooks.register(
                HookPhase.BEFORE_COMPOSE_RENDER,
                self.configure_vscode,
                key=("cloudcli", "inject_vscode"),
                name="inject CloudCLI into VSCode Compose",
            )

    def configure_vscode(self):
        """Run CloudCLI alongside code-server, sharing its tools and projects."""
        if not self.enable:
            return
        script = self.get_source_path("scripts/20-cloudcli.sh")
        if not script.is_file() or not os.access(script, os.X_OK):
            raise ContainerError(f"CloudCLI startup script is unavailable: {script}")

        vscode = self.containers["vscode"]
        vscode.volumes[f"/entrypoint.d/{script.name}"] = {"source": str(script), "read_only": True}
        vscode.volumes["/workspace/.cloudcli"] = str(self.get_app_path("home/.cloudcli"))
        port = self.get_config("CLOUD_CLI_PORT")
        if port > 0:
            vscode.ports[port] = 3001

        vscode.add_start_hook(
            ("cloudcli", "prepare_data"),
            self._prepare_data,
            name="prepare CloudCLI data directory",
        )

    def _prepare_data(self):
        path = self.get_app_path("home/.cloudcli")
        os.makedirs(path, exist_ok=True)
        self.runtime.chown(path, self.get_config("DOCKER_USER"))

    @cached_property
    def integrations(self) -> "Integrations":
        return endpoint(
            self,
            domain=ConfigRef("CLOUD_CLI_DOMAIN"),
            proxy="http://code-server:3001",
            auth_bypass=(r"\.(css|js)$",),
            extensions=[
                Flare.links(
                    Flare.public(),
                    Flare.container(
                        url=load_port_url(ConfigRef("CLOUD_CLI_PORT"), https=False),
                    ),
                    name="CloudCLI",
                    icon="messageOutline",
                    desc="Cloud CLI",
                ),
            ],
        )
