#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@author  : Hu Ji
@file    : deploy.py 
@time    : 2023/05/21
@site    :  
@software: PyCharm 

              ,----------------,              ,---------,
         ,-----------------------,          ,"        ,"|
       ,"                      ,"|        ,"        ,"  |
      +-----------------------+  |      ,"        ,"    |
      |  .-----------------.  |  |     +---------+      |
      |  |                 |  |  |     | -==----'|      |
      |  | $ sudo rm -rf / |  |  |     |         |      |
      |  |                 |  |  |/----|`---=    |      |
      |  |                 |  |  |   ,/|==== ooo |      ;
      |  |                 |  |  |  // |(((( [33]|    ,"
      |  `-----------------'  |," .;'| |((((     |  ,"
      +-----------------------+  ;;  | |         |,"
         /_)______________(_/  //'   | +---------+
    ___________________________/___  `,
   /  oooooooooooooooo  .o.  oooo /,   `,"-----------
  / ==ooooooooooooooo==.o.  ooo= //   ,``--{)B     ,"
 /_==__==========__==_ooo__ooo=_/'   /___________,"
"""
import uuid
import re
from linktools.runtime import lazy_load
from typing import Iterable

from linktools.cntr import BaseContainer, Integrations, NginxSite
from linktools.core import ConfigField, AliasProvider, LazyProvider, PromptProvider
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            XRAY_TAG="latest",
            XRAY_DOMAIN=self.get_nginx_domain(),
            XRAY_ID=ConfigField(provider=LazyProvider(lambda r: str(uuid.uuid4()), cached=True)),
            XRAY_WEBSOCKET_PATH=ConfigField.chain(
                AliasProvider("XRAY_PATH"),
                PromptProvider(default="/i/am/websocket", cached=True),
            ),
            XRAY_GRPC_SERVICE_NAME=ConfigField(provider=PromptProvider(default="/i/am/grpc", cached=True)),
            XRAY_XHTTP_PATH=ConfigField(provider=PromptProvider(default="/i/am/xhttp", cached=True)),
        )

    @cached_property
    def integrations(self) -> Integrations:
        grpc_pattern = lazy_load(lambda: "^" + re.escape(
            self.get_route_path("XRAY_GRPC_SERVICE_NAME")) + r"(?:/(?:Tun|TunMulti))?$")
        xhttp_pattern = lazy_load(lambda: "^" + re.escape(
            self.get_route_path("XRAY_XHTTP_PATH")) + r"(?:/|$)")
        return {"nginx": {"web": NginxSite(
            server_name=self.get_config_later("XRAY_DOMAIN"),
            template=self.get_source_path("nginx.conf"),
            auth=False,
            waf_bypass=(grpc_pattern, xhttp_pattern),
            vars={
                "websocket_path": lazy_load(lambda: self.get_route_path("XRAY_WEBSOCKET_PATH")),
                "grpc_path": lazy_load(lambda: self.get_route_path("XRAY_GRPC_SERVICE_NAME")),
                "grpc_pattern": grpc_pattern,
                "xhttp_path": lazy_load(lambda: self.get_route_path("XRAY_XHTTP_PATH")),
            },
        )}}

    def get_route_path(self, key: str) -> str:
        """Use one root-relative path in the proxy and application config."""
        return "/" + self.get_config(key).strip("/")

    def on_starting(self):
        self.render_template(
            self.get_source_path("config.json"),
            self.get_app_path("config.json", create_parent=True),
        )
