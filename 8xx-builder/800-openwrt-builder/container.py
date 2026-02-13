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
import os

from linktools import utils
from linktools.cli import subcommand, subcommand_argument
from linktools.cntr import BaseContainer
from linktools.core import Config
from linktools.decorator import cached_property
from linktools.rich import choose


class Container(BaseContainer):
    """build openwrt image"""

    @cached_property
    def configs(self):
        return dict(
            OPENWRT_BUILD_PATH=Config.Prompt(cached=True, type="path"),
        )

    @subcommand("update")
    def on_exec_update(self):
        self.manager.create_docker_process(
            "exec", self.get_service_name("openwrt_builder"), "git", "pull"
        ).check_call()
        self.manager.create_docker_process(
            "exec", self.get_service_name("openwrt_builder"), "./scripts/feeds", "update", "-a"
        ).check_call()
        self.manager.create_docker_process(
            "exec", self.get_service_name("openwrt_builder"), "./scripts/feeds", "install", "-a"
        ).check_call()

    @subcommand("config")
    def on_exec_config(self):
        self.manager.create_docker_process(
            "exec", "-it", self.get_service_name("openwrt_builder"), "make", "menuconfig"
        ).check_call()

    @subcommand("choose")
    def on_exec_choose(self):
        config_names = []
        config_path = os.path.join(os.path.dirname(__file__), "configs")
        for config_name in os.listdir(config_path):
            if config_name[:1].isalpha() and config_name.endswith(".config"):
                config_names.append(config_name[:-len(".config")])

        config_name = choose(
            f"Choose config",
            choices=config_names,
        )

        self.manager.create_docker_process(
            "exec", "-it", self.get_service_name("openwrt_builder"),
            "sh", "-c", utils.list2cmdline([
                "ln", "-sf",
                f"/home/user/configs/{config_name}.config",
                f"/home/user/openwrt/.config"
            ])
        ).call()

    @subcommand("download")
    @subcommand_argument("-j", "--jobs")
    def on_exec_download(self, jobs: int = 8):
        self.manager.create_docker_process(
            "exec", "-it", self.get_service_name("openwrt_builder"), "make", "download", f"-j{jobs}"
        ).call()

    @subcommand("build")
    @subcommand_argument("-j", "--jobs")
    def on_exec_build(self, jobs: int = 8):
        self.manager.create_docker_process(
            "exec", "-it", self.get_service_name("openwrt_builder"), "make", "V=s", f"-j{jobs}"
        ).call()

    def on_started(self):
        self.manager.create_docker_process(
            "exec", self.get_service_name("openwrt_builder"),
            "git", "config", "--global", "http.sslverify", "false"
        ).call()
