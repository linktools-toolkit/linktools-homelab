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
from linktools.cntr.ext import Authelia, load_nginx_url, Nginx, Flare, load_config_url
from linktools.decorator import cached_property
from linktools.runtime import lazy_load


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["flare"]

    @cached_property
    def configs(self):
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
        return (
            Nginx.site(
                local_id="pve",
                expose=Flare.public("Proxmox", "server", "虚拟化环境"),
                server_name=lazy_load(lambda: self.get_config("PVE_DOMAIN") if self.get_config("PVE_LOCAL_URL") else ""),
                proxy=self.get_config_later("PVE_LOCAL_URL"),
                auth=None,
            ),
            Nginx.site(
                local_id="primary_gateway",
                expose=Flare.public("GW1", "RouterNetwork", "主路由管理"),
                server_name=lazy_load(lambda: self.get_config("PRIMARY_GATEWAY_DOMAIN") if self.get_config("PRIMARY_GATEWAY_LOCAL_URL") else ""),
                proxy=self.get_config_later("PRIMARY_GATEWAY_LOCAL_URL"),
                auth=None,
                auth_headers={"Authorization": self.get_config_later("PRIMARY_GATEWAY_AUTHORIZATION")},
            ),
            Nginx.site(
                local_id="bypass_gateway",
                expose=Flare.public("GW2", "RouterNetwork", "旁路由管理"),
                server_name=lazy_load(lambda: self.get_config("BYPASS_GATEWAY_DOMAIN") if self.get_config("BYPASS_GATEWAY_LOCAL_URL") else ""),
                proxy=self.get_config_later("BYPASS_GATEWAY_LOCAL_URL"),
                auth=None,
                auth_headers={"Authorization": self.get_config_later("BYPASS_GATEWAY_AUTHORIZATION")},
            ),
            Nginx.site(
                local_id="xiaoya_alist",
                expose=Flare.public("Xiaoya-Alist", "folderSync", "小雅Alist"),
                server_name=lazy_load(lambda: self.get_config("XIAOYA_ALIST_DOMAIN") if self.get_config("XIAOYA_ALIST_LOCAL_URL") else ""),
                proxy=self.get_config_later("XIAOYA_ALIST_LOCAL_URL"),
                auth=False,
            ),
            Nginx.site(
                local_id="emby",
                expose=Flare.public("Emby", "movie", "Emby"),
                server_name=lazy_load(lambda: self.get_config("EMBY_DOMAIN") if self.get_config("EMBY_LOCAL_URL") else ""),
                proxy=self.get_config_later("EMBY_LOCAL_URL"),
                auth=False,
            ),
            Nginx.site(
                local_id="jellyfin",
                expose=Flare.public("Jellyfin", "movie", "jellyfin"),
                server_name=lazy_load(lambda: self.get_config("JELLYFIN_DOMAIN") if self.get_config("JELLYFIN_LOCAL_URL") else ""),
                proxy=self.get_config_later("JELLYFIN_LOCAL_URL"),
                auth=False,
            ),
            Flare.category("private")("Proxmox", "server", "虚拟化环境", load_config_url(self, "PVE_LOCAL_URL")),
            Flare.category("private")("GW1", "RouterNetwork", "主路由管理", load_config_url(self, "PRIMARY_GATEWAY_LOCAL_URL")),
            Flare.category("private")("GW2", "RouterNetwork", "旁路由管理", load_config_url(self, "BYPASS_GATEWAY_LOCAL_URL")),
            Flare.category("private")("Xiaoya-Alist", "folderSync", "小雅Alist", load_config_url(self, "XIAOYA_ALIST_LOCAL_URL")),
            Flare.category("private")("Emby", "movie", "Emby", load_config_url(self, "EMBY_LOCAL_URL")),
            Flare.category("private")("Jellyfin", "movie", "jellyfin", load_config_url(self, "JELLYFIN_LOCAL_URL")),
            Authelia.oidc(
                redirect_uris=(load_nginx_url(self, "pve"), self.get_config_later("PVE_LOCAL_URL")),
                enabled=lazy_load(lambda: self.get_config("NGINX_AUTH_ENABLE")
                                  and bool(load_nginx_url(self, "pve"))),
            ),
        )
