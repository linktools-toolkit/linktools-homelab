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

from linktools.cntr import BaseContainer, Integrations, NginxSite
from linktools.decorator import cached_property
from linktools.runtime import lazy_load


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["flare"]

    @cached_property
    def configs(self):
        return dict(
            PVE_DOMAIN=self.get_nginx_domain("pve"),
            PVE_LOCAL_URL="",

            PRIMARY_GATEWAY_DOMAIN=self.get_nginx_domain("gw1"),
            PRIMARY_GATEWAY_LOCAL_URL="",
            PRIMARY_GATEWAY_AUTHORIZATION="",

            BYPASS_GATEWAY_DOMAIN=self.get_nginx_domain("gw2"),
            BYPASS_GATEWAY_LOCAL_URL="",
            BYPASS_GATEWAY_AUTHORIZATION="",

            XIAOYA_ALIST_DOMAIN=self.get_nginx_domain("xiaoya-alist"),
            XIAOYA_ALIST_LOCAL_URL="",

            EMBY_DOMAIN=self.get_nginx_domain("emby"),
            EMBY_LOCAL_URL="",

            JELLYFIN_DOMAIN=self.get_nginx_domain("jellyfin"),
            JELLYFIN_LOCAL_URL="",
        )

    @cached_property
    def integrations(self) -> Integrations:
        return {
            "nginx": {
                "pve": NginxSite(
                    expose=self.expose_public("Proxmox", "server", "虚拟化环境"),
                    server_name=lazy_load(lambda: self.get_config("PVE_DOMAIN") if self.get_config("PVE_LOCAL_URL") else ""),
                    proxy=self.get_config_later("PVE_LOCAL_URL"),
                    auth=None,
                    oidc_redirects=("", self.get_config_later("PVE_LOCAL_URL")) if self.get_config("NGINX_AUTH_ENABLE") else (),
                ),
                "primary_gateway": NginxSite(
                    expose=self.expose_public("GW1", "RouterNetwork", "主路由管理"),
                    server_name=lazy_load(lambda: self.get_config("PRIMARY_GATEWAY_DOMAIN") if self.get_config("PRIMARY_GATEWAY_LOCAL_URL") else ""),
                    proxy=self.get_config_later("PRIMARY_GATEWAY_LOCAL_URL"),
                    auth=None,
                    auth_headers={"Authorization": self.get_config_later("PRIMARY_GATEWAY_AUTHORIZATION")},
                ),
                "bypass_gateway": NginxSite(
                    expose=self.expose_public("GW2", "RouterNetwork", "旁路由管理"),
                    server_name=lazy_load(lambda: self.get_config("BYPASS_GATEWAY_DOMAIN") if self.get_config("BYPASS_GATEWAY_LOCAL_URL") else ""),
                    proxy=self.get_config_later("BYPASS_GATEWAY_LOCAL_URL"),
                    auth=None,
                    auth_headers={"Authorization": self.get_config_later("BYPASS_GATEWAY_AUTHORIZATION")},
                ),
                "xiaoya_alist": NginxSite(
                    expose=self.expose_public("Xiaoya-Alist", "folderSync", "小雅Alist"),
                    server_name=lazy_load(lambda: self.get_config("XIAOYA_ALIST_DOMAIN") if self.get_config("XIAOYA_ALIST_LOCAL_URL") else ""),
                    proxy=self.get_config_later("XIAOYA_ALIST_LOCAL_URL"),
                    auth=False,
                ),
                "emby": NginxSite(
                    expose=self.expose_public("Emby", "movie", "Emby"),
                    server_name=lazy_load(lambda: self.get_config("EMBY_DOMAIN") if self.get_config("EMBY_LOCAL_URL") else ""),
                    proxy=self.get_config_later("EMBY_LOCAL_URL"),
                    auth=False,
                ),
                "jellyfin": NginxSite(
                    expose=self.expose_public("Jellyfin", "movie", "jellyfin"),
                    server_name=lazy_load(lambda: self.get_config("JELLYFIN_DOMAIN") if self.get_config("JELLYFIN_LOCAL_URL") else ""),
                    proxy=self.get_config_later("JELLYFIN_LOCAL_URL"),
                    auth=False,
                ),
            },
            "flare": {
                "pve_private": self.expose_private("Proxmox", "server", "虚拟化环境", self.load_config_url("PVE_LOCAL_URL")),
                "primary_gateway_private": self.expose_private("GW1", "RouterNetwork", "主路由管理", self.load_config_url("PRIMARY_GATEWAY_LOCAL_URL")),
                "bypass_gateway_private": self.expose_private("GW2", "RouterNetwork", "旁路由管理", self.load_config_url("BYPASS_GATEWAY_LOCAL_URL")),
                "xiaoya_alist_private": self.expose_private("Xiaoya-Alist", "folderSync", "小雅Alist", self.load_config_url("XIAOYA_ALIST_LOCAL_URL")),
                "emby_private": self.expose_private("Emby", "movie", "Emby", self.load_config_url("EMBY_LOCAL_URL")),
                "jellyfin_private": self.expose_private("Jellyfin", "movie", "jellyfin", self.load_config_url("JELLYFIN_LOCAL_URL")),
            },
        }
