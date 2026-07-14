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

from linktools.cntr import BaseContainer
from linktools.core import ConfigField, AliasProvider, PromptProvider
from linktools.decorator import cached_property


class Container(BaseContainer):

    @cached_property
    def configs(self):
        return dict(
            ALI_DDNS_TAG="latest",
            ALI_DDNS_DOMAIN=ConfigField.chain(
                AliasProvider("ROOT_DOMAIN"), AliasProvider("NGINX_ROOT_DOMAIN"),
                PromptProvider(cached=True),
            ),
            ALI_DDNS_ROOT_DOMAIN=ConfigField.chain(
                AliasProvider("ROOT_DOMAIN"), AliasProvider("NGINX_ROOT_DOMAIN"),
                PromptProvider(cached=True),
            ),
            ALI_DDNS_KEY=ConfigField.chain(
                AliasProvider("Ali_Key"),
                PromptProvider(cached=True),
            ),
            ALI_DDNS_SECRET=ConfigField.chain(
                AliasProvider("Ali_Secret"),
                PromptProvider(cached=True),
            ),
            ALI_DDNS_CHECKLOCAL=ConfigField(cast=bool, default=False),
            ALI_DDNS_IPV4NETS="",
            ALI_DDNS_IPV6NETS="",
        )
