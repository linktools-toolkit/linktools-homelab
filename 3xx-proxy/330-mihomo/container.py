#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Iterable

from linktools import utils
from linktools.cntr import BaseContainer, EventContext, ExposeLink
from linktools.core import Config
from linktools.decorator import cached_property


class Container(BaseContainer):

    @cached_property
    def configs(self):
        return dict(
            MIHOMO_TAG="Alpha",
            MIHOMO_DOMAIN=self.get_nginx_domain(),
            MIHOMO_PORT=Config.Alias(type=int, default=9090),
            MIHOMO_HTTP_PROXY_PORT=Config.Alias(type=int, default=7890),
            MIHOMO_SOCKS_PROXY_PORT=Config.Alias(type=int, default=7891),
            MIHOMO_CONFIG_FILE="config.yaml",
            MIHOMO_SUBSCRIBE_URL=Config.Prompt(cached=True),
            MIHOMO_SUBSCRIBE_USER_AGENT=Config.Alias(default="mihomo-subscription-updater/1.0"),
            MIHOMO_SECRET=Config.Alias(cached=True) | utils.make_uuid()[:12],
            MIHOMO_EXTERNAL_UI_NAME="metacubexd",
            MIHOMO_EXTERNAL_UI_URL="https://gh-proxy.com/github.com/MetaCubeX/metacubexd/archive/refs/heads/gh-pages.zip",
            MIHOMO_GEOIP_METADB_URL="https://gh-proxy.com/github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geoip.metadb",
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("Mihomo", "vpn", "Mihomo监控", self.load_nginx_url(
                "MIHOMO_DOMAIN", "ui", "metacubexd", "#", "setup",
                queries=dict(
                    hostname=self.get_config_later(Config.Property("MIHOMO_DOMAIN")),
                    port=self.get_config_later("NGINX_HTTPS_PORT"),
                    secret=self.get_config_later("MIHOMO_SECRET"),
                ),
                proxy_name="mihomo",
                proxy_url="http://mihomo:9090",
                auth_enable=True,
            )),
            self.expose_container("Mihomo", "vpn", "Mihomo监控", self.load_port_url(
                "MIHOMO_PORT", "ui", "metacubexd", "#", "setup",
                queries=dict(
                    hostname=self.get_config_later("HOST"),
                    port=self.get_config_later("MIHOMO_PORT"),
                    secret=self.get_config_later("MIHOMO_SECRET"),
                ),
                https=False,
            )),
        ]

    def on_starting(self, context: EventContext):
        if "pull" in (context.commands or []):
            utils.remove_file(self.get_app_path("config", "geoip.metadb"))
            utils.remove_file(self.get_app_path("config", "ui"))
