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
from linktools.cntr import BaseContainer, Integrations
from linktools.cntr.ext import Nginx, Flare, load_port_url, load_nginx_url
from linktools.core import ConfigField
from linktools.decorator import cached_property


class Container(BaseContainer):

    @cached_property
    def configs(self):
        return dict(
            QBITTORRENT_TAG="latest",
            QBITTORRENT_DOMAIN=Nginx.domain(self),
            QBITTORRENT_PORT=ConfigField(cast=int, default=0),
            QBITTORRENT_TORRENTING_PORT=ConfigField(cast=int, default=6881),
        )

    @cached_property
    def integrations(self) -> Integrations:
        return (
            {"web": Nginx.site(
                server_name=self.get_config_later("QBITTORRENT_DOMAIN"),
                template=self.get_source_path("nginx.conf"),
                auth=False,
            )},
            Flare.public("qBittorrent", "tools", "", load_nginx_url(self, "web")),
            Flare.container("qBittorrent", "tools", load_port_url(
                self, "QBITTORRENT_PORT",
                https=False
            ), desc=""),
        )
