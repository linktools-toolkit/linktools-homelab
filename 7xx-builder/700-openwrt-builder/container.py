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
from typing import Iterable

from linktools import utils
from linktools.cli import subcommand, subcommand_argument
from linktools.cntr import BaseContainer
from linktools.core import Config
from linktools.decorator import cached_property
from linktools.rich import choose


class Container(BaseContainer):
    """build openwrt image"""

    @property
    def dependencies(self) -> Iterable[str]:
        return ["coder"]

    @cached_property
    def configs(self):
        return dict(
            OPENWRT_BUILD_PATH=Config.Lazy(lambda cfg: utils.join_path(cfg.get("CODER_PROJECT_PATH"), "openwrt")),
        )

    @subcommand("update")
    def on_exec_update(self):
        self.manager.create_docker_process(
            "exec", self.get_service_name("openwrt_builder"), "git", "stash"
        ).check_call()
        self.manager.create_docker_process(
            "exec", self.get_service_name("openwrt_builder"), "git", "pull"
        ).check_call()
        self.manager.create_docker_process(
            "exec", self.get_service_name("openwrt_builder"), "git", "stash", "pop"
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
                f"/data/configs/{config_name}.config",
                f"/data/openwrt/.config"
            ])
        ).call()

    @subcommand("download", pass_args=True)
    @subcommand_argument("-j", "--jobs")
    def on_exec_download(self, jobs: int = 8):
        args = ["make", "download", f"-j{jobs}"]
        if self.manager.debug:
            args.append("V=s")
        self.manager.create_docker_process(
            "exec", "-it", self.get_service_name("openwrt_builder"), *args,
        ).call()

    @subcommand("build")
    @subcommand_argument("-j", "--jobs")
    def on_exec_build(self, jobs: int = 8):
        args = ["make", "V=s", f"-j{jobs}"]
        if self.manager.debug:
            args.append("V=s")
        self.manager.create_docker_process(
            "exec", "-it", self.get_service_name("openwrt_builder"), *args,
        ).call()

    def on_started(self):
        self.manager.create_docker_process(
            "exec", self.get_service_name("openwrt_builder"),
            "git", "config", "--global", "http.sslverify", "false"
        ).call()
        self.manager.create_docker_process(
            "exec", self.get_service_name("openwrt_builder"),
            "git", "config", "pull.rebase", "true"
        ).call()
