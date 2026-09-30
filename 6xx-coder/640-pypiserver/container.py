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
from linktools.core import ConfigField, PromptProvider
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            PYPISERVER_TAG="latest",
            PYPISERVER_DOMAIN=self.get_nginx_domain("pypi"),
            PYPISERVER_PORT=ConfigField(cast=int, default=0),
            PYPISERVER_USERNAME=ConfigField(provider=PromptProvider(cached=True)),
            PYPISERVER_PASSWORD=ConfigField(provider=PromptProvider(cached=True)),
            PYPISERVER_AUTHENTICATE="update",  # "update,download,list"
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("pypiserver", "languagePython", "pypiserver", self.load_nginx_url(
                "PYPISERVER_DOMAIN", "simple",
                proxy_conf=self.get_source_path("nginx.conf"),
            )),
            self.expose_container("pypiserver", "languagePython", "pypiserver", self.load_port_url(
                "PYPISERVER_PORT",
                https=False
            )),
        ]

    def on_starting(self):
        path = self.get_app_data_path("auth", ".htpasswd", create_parent=True)
        with open(path, "wt") as fd:
            username = self.get_config('PYPISERVER_USERNAME')
            password = self.get_config('PYPISERVER_PASSWORD')
            fd.write(f"{username}:{password}")
