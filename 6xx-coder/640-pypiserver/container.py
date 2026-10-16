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

from linktools.cntr import OperationContext, BaseContainer, Integrations
from linktools.cntr.ext import Nginx, Flare, load_port_url, endpoint
from linktools.core import ConfigField, PromptProvider, ConfigRef
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def fields(self):
        return dict(
            PYPISERVER_TAG="latest",
            PYPISERVER_DOMAIN=Nginx.domain(self, "pypi"),
            PYPISERVER_PORT=ConfigField(cast=int, default=0),
            PYPISERVER_USERNAME=ConfigField(provider=PromptProvider(cached=True)),
            PYPISERVER_PASSWORD=ConfigField(provider=PromptProvider(cached=True)),
            PYPISERVER_AUTHENTICATE="update",  # "update,download,list"
        )

    @cached_property
    def integrations(self) -> Integrations:
        return endpoint(
            self,
            domain=ConfigRef("PYPISERVER_DOMAIN"),
            template=self.get_source_path("nginx.conf"),
            auth=False,
            extensions=[
                Flare.links(
                    Flare.public(
                        url="{base_url}/simple",
                    ),
                    Flare.container(
                        url=load_port_url(ConfigRef("PYPISERVER_PORT"), https=False),
                    ),
                    name="pypiserver",
                    icon="languagePython",
                    desc="pypiserver",
                ),
            ],
        )

    def on_starting(self, context: OperationContext):
        username = self.get_config("PYPISERVER_USERNAME")
        password = self.get_config("PYPISERVER_PASSWORD")
        content = f"{username}:{password}"
        path = self.get_app_data_path("auth", ".htpasswd", create_parent=True)
        with open(path, "wt") as fd:
            fd.write(content)
