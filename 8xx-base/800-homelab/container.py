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
from typing import Iterable

from linktools.cntr import BaseContainer, Integrations
from linktools.cntr.ext import Authelia, Nginx, Flare, load_config_url, endpoint
from linktools.core import ConfigRef
from linktools.decorator import cached_property
from linktools.runtime import lazy_load


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["flare"]

    @cached_property
    def fields(self):
        return dict(
            PVE_DOMAIN=Nginx.domain(self, "pve"),
            PVE_LOCAL_URL="",

            PRIMARY_GATEWAY_DOMAIN=Nginx.domain(self, "gw1"),
            PRIMARY_GATEWAY_LOCAL_URL="",
            PRIMARY_GATEWAY_AUTHORIZATION="",

            BYPASS_GATEWAY_DOMAIN=Nginx.domain(self, "gw2"),
            BYPASS_GATEWAY_LOCAL_URL="",
            BYPASS_GATEWAY_AUTHORIZATION="",

            XIAOYA_ALIST_DOMAIN=Nginx.domain(self, "xiaoya-alist"),
            XIAOYA_ALIST_LOCAL_URL="",

            EMBY_DOMAIN=Nginx.domain(self, "emby"),
            EMBY_LOCAL_URL="",

            JELLYFIN_DOMAIN=Nginx.domain(self, "jellyfin"),
            JELLYFIN_LOCAL_URL="",
        )

    @cached_property
    def integrations(self) -> Integrations:
        return [
            endpoint(
                self,
                domain=lazy_load(
                    lambda: (
                        self.get_config("PVE_DOMAIN")
                        if self.get_config("PVE_LOCAL_URL")
                        else ""
                    )
                ),
                proxy=ConfigRef("PVE_LOCAL_URL"),
                auth=None,
                extensions=[
                    Flare.public("Proxmox", "server", "虚拟化环境"),
                    Authelia.oidc(
                        redirect_uris=("{base_url}", ConfigRef("PVE_LOCAL_URL")),
                    ),
                ],
            ),
            endpoint(
                self,
                domain=lazy_load(
                    lambda: (
                        self.get_config("PRIMARY_GATEWAY_DOMAIN")
                        if self.get_config("PRIMARY_GATEWAY_LOCAL_URL")
                        else ""
                    )
                ),
                proxy=ConfigRef("PRIMARY_GATEWAY_LOCAL_URL"),
                auth=None,
                auth_headers={
                    "Authorization": ConfigRef(
                        "PRIMARY_GATEWAY_AUTHORIZATION"
                    ),
                },
                extensions=[Flare.public("GW1", "RouterNetwork", "主路由管理")],
            ),
            endpoint(
                self,
                domain=lazy_load(
                    lambda: (
                        self.get_config("BYPASS_GATEWAY_DOMAIN")
                        if self.get_config("BYPASS_GATEWAY_LOCAL_URL")
                        else ""
                    )
                ),
                proxy=ConfigRef("BYPASS_GATEWAY_LOCAL_URL"),
                auth=None,
                auth_headers={
                    "Authorization": ConfigRef(
                        "BYPASS_GATEWAY_AUTHORIZATION"
                    ),
                },
                extensions=[Flare.public("GW2", "RouterNetwork", "旁路由管理")],
            ),
            endpoint(
                self,
                domain=lazy_load(
                    lambda: (
                        self.get_config("XIAOYA_ALIST_DOMAIN")
                        if self.get_config("XIAOYA_ALIST_LOCAL_URL")
                        else ""
                    )
                ),
                proxy=ConfigRef("XIAOYA_ALIST_LOCAL_URL"),
                auth=False,
                waf_bypass=(r"^/soutv",),
                extensions=[Flare.public("Xiaoya-Alist", "folderSync", "小雅Alist")],
            ),
            endpoint(
                self,
                domain=lazy_load(
                    lambda: (
                        self.get_config("EMBY_DOMAIN")
                        if self.get_config("EMBY_LOCAL_URL")
                        else ""
                    )
                ),
                proxy=ConfigRef("EMBY_LOCAL_URL"),
                auth=False,
                extensions=[Flare.public("Emby", "movie", "Emby")],
            ),
            endpoint(
                self,
                domain=lazy_load(
                    lambda: (
                        self.get_config("JELLYFIN_DOMAIN")
                        if self.get_config("JELLYFIN_LOCAL_URL")
                        else ""
                    )
                ),
                proxy=ConfigRef("JELLYFIN_LOCAL_URL"),
                auth=False,
                extensions=[Flare.public("Jellyfin", "movie", "jellyfin")],
            ),
            Flare.category("private")(
                "Proxmox",
                "server",
                "虚拟化环境",
                load_config_url(ConfigRef("PVE_LOCAL_URL", type=str)),
            ),
            Flare.category("private")(
                "GW1",
                "RouterNetwork",
                "主路由管理",
                load_config_url(ConfigRef("PRIMARY_GATEWAY_LOCAL_URL", type=str)),
            ),
            Flare.category("private")(
                "GW2",
                "RouterNetwork",
                "旁路由管理",
                load_config_url(ConfigRef("BYPASS_GATEWAY_LOCAL_URL", type=str)),
            ),
            Flare.category("private")(
                "Xiaoya-Alist",
                "folderSync",
                "小雅Alist",
                load_config_url(ConfigRef("XIAOYA_ALIST_LOCAL_URL", type=str)),
            ),
            Flare.category("private")(
                "Emby",
                "movie",
                "Emby",
                load_config_url(ConfigRef("EMBY_LOCAL_URL", type=str)),
            ),
            Flare.category("private")(
                "Jellyfin",
                "movie",
                "jellyfin",
                load_config_url(ConfigRef("JELLYFIN_LOCAL_URL", type=str)),
            ),
        ]
