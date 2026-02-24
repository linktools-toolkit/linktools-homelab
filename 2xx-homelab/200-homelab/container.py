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

from linktools.cntr import BaseContainer, ExposeLink
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["flare"]

    @cached_property
    def configs(self):
        return dict(
            PVE_DOMAIN=self.get_nginx_domain("pve"),
            PVE_LOCAL_URL="https://10.10.10.254:8006",

            PRIMARY_GATEWAY_DOMAIN=self.get_nginx_domain("gw1"),
            PRIMARY_GATEWAY_LOCAL_URL="http://10.10.10.253:80",
            PRIMARY_GATEWAY_AUTHORIZATION="",

            BYPASS_GATEWAY_DOMAIN=self.get_nginx_domain("gw2"),
            BYPASS_GATEWAY_LOCAL_URL="http://10.10.10.252:80",
            BYPASS_GATEWAY_AUTHORIZATION="",

            XIAOYA_ALIST_LOCAL_URL="",
            XIAOYA_ALIST_DOMAIN="",

            EMBY_LOCAL_URL="",
            EMBY_DOMAIN="",

            JELLYFIN_LOCAL_URL="",
            JELLYFIN_DOMAIN="",
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("Proxmox", "server", "虚拟化环境", self.load_nginx_url(
                "PVE_DOMAIN",
                proxy_name="pve",
                proxy_url=self.get_config_later("PVE_LOCAL_URL"),
                auth_enable=True,
                auth_extra={
                    "oidc_redirect_uris": [""],
                }
            )),
            self.expose_private("Proxmox", "server", "虚拟化环境", self.load_config_url(
                "PVE_LOCAL_URL"
            )),

            self.expose_public("GW1", "RouterNetwork", "主路由管理", self.load_nginx_url(
                "PRIMARY_GATEWAY_DOMAIN",
                proxy_name="primary-gateway",
                proxy_url=self.get_config_later("PRIMARY_GATEWAY_LOCAL_URL"),
                auth_enable=True,
                auth_extra={
                    "headers": {
                        "Authorization": self.get_config("PRIMARY_GATEWAY_AUTHORIZATION")
                    },
                },
            )),
            self.expose_private("GW1", "RouterNetwork", "主路由管理", self.load_config_url(
                "PRIMARY_GATEWAY_LOCAL_URL"
            )),

            self.expose_public("GW2", "RouterNetwork", "旁路由管理", self.load_nginx_url(
                "BYPASS_GATEWAY_DOMAIN",
                proxy_name="bypass-gateway",
                proxy_url=self.get_config_later("BYPASS_GATEWAY_LOCAL_URL"),
                auth_enable=True,
                auth_extra={
                    "headers": {
                        "Authorization": self.get_config("BYPASS_GATEWAY_AUTHORIZATION")
                    },
                },
            )),
            self.expose_private("GW2", "RouterNetwork", "旁路由管理", self.load_config_url(
                "BYPASS_GATEWAY_LOCAL_URL"
            )),

            self.expose_public("Xiaoya-Alist", "folderSync", "小雅Alist", self.load_nginx_url(
                "XIAOYA_ALIST_DOMAIN",
                proxy_name="xiaoya-alist",
                proxy_url=self.get_config_later("XIAOYA_ALIST_LOCAL_URL"),
                # auth_enable=True,
            )),
            self.expose_private("Xiaoya-Alist", "folderSync", "小雅Alist", self.load_config_url(
                "XIAOYA_ALIST_LOCAL_URL"
            )),

            self.expose_public("Emby", "movie", "Emby", self.load_nginx_url(
                "EMBY_DOMAIN",
                proxy_name="emby",
                proxy_url=self.get_config_later("EMBY_LOCAL_URL"),
            )),
            self.expose_private("Emby", "movie", "Emby", self.load_config_url(
                "EMBY_LOCAL_URL"
            )),

            self.expose_public("Jellyfin", "movie", "jellyfin", self.load_nginx_url(
                "JELLYFIN_DOMAIN",
                proxy_name="jellyfin",
                proxy_url=self.get_config_later("JELLYFIN_LOCAL_URL"),
            )),
            self.expose_private("Jellyfin", "movie", "jellyfin", self.load_config_url(
                "JELLYFIN_LOCAL_URL"
            )),
        ]
