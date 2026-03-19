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
import os.path
import subprocess
from pathlib import Path
from typing import Iterable

from linktools import utils
from linktools.cli import subcommand, subcommand_argument
from linktools.cntr import BaseContainer
from linktools.core import Config
from linktools.decorator import cached_property


class Container(BaseContainer):
    """build android image"""

    @property
    def dependencies(self) -> Iterable[str]:
        return ["coder"]

    @cached_property
    def configs(self):
        return dict(
            REDROID_BUILD_PATH=Config.Lazy(lambda cfg: utils.join_path(cfg.get("CODER_PROJECT_PATH"), "redroid")),
        )

    @subcommand("init-repo", help="Initialize redroid repo")
    @subcommand_argument(
        "-u", "--manifest-url", metavar="URL",
        default="https://github.com/redroid-rockchip/platform_manifests.git",
        help="manifest repository location")
    @subcommand_argument(
        "-b", "--manifest-branch", metavar="REVISION",
        default="redroid-12.0.0",
        help="manifest branch or revision (use HEAD for default)")
    def on_exec_repo_init(self, manifest_url: str, manifest_branch: str):
        self.manager.create_docker_process(
            "exec", "-it", self.get_service_name("redroid-builder"),
            "repo", "init", "-u", manifest_url, "-b", manifest_branch, "--depth=1", "--git-lfs",
        ).check_call()

    @subcommand("sync-repo", help="Sync redroid repo")
    def on_exec_repo_sync(self):
        self.manager.create_docker_process(
            "exec", "-it", self.get_service_name("redroid-builder"),
            "repo", "sync", "-c",
        ).check_call()

        self.manager.create_docker_process(
            "exec", "-it", self.get_service_name("redroid-builder"),
            "repo", "forall", "-g", "lfs", "-c", "git", "lfs", "pull",
        ).check_call()

    @subcommand("build-rk3588", help="Build rk3588 redroid arm64 image")
    def on_exec_build_rk3588(self):
        self.manager.create_docker_process(
            "exec", "-it", self.get_service_name("redroid-builder"),
            "build-rk3588",
        ).check_call()

    @subcommand("make-image", help="Build redroid arm64 image")
    def on_exec_make_arm64_image(self):
        p1 = p2 = None
        path = os.path.join(
            self.get_config("REDROID_BUILD_PATH", type="path"),
            "out", "target", "product", "redroid_arm64"
        )

        try:
            self.manager.create_process(
                "sh", "-c", "mount system.img system -o ro",
                cwd=path,
                privilege=True
            ).check_call()

            self.manager.create_process(
                "sh", "-c", "mount vendor.img vendor -o ro",
                cwd=path,
                privilege=True
            ).check_call()

            p1 = self.manager.create_process(
                "sh", "-c", "tar --xattrs -c vendor -C system --exclude=\"./vendor\" . ",
                cwd=path,
                stdout=subprocess.PIPE,
                privilege=True
            )

            p2 = self.manager.create_docker_process(
                "import",
                "-c", "ENTRYPOINT [\"/init\", \"androidboot.hardware=redroid\"]",
                "--platform", "linux/arm64",
                "-", "redroid",
                append_env=dict(DOCKER_DEFAULT_PLATFORM="linux/arm64"),
                stdin=p1.stdout
            )

            p1.wait()
            p2.wait()

        finally:
            if p1:
                utils.ignore_errors(p1.kill)
            if p2:
                utils.ignore_errors(p2.kill)

            self.manager.create_process(
                "sh", "-c", "umount system vendor",
                cwd=path,
                privilege=True
            ).call()

    @subcommand("fix-permission", help="fix redroid source permission")
    def on_exec_fix_permission(self):
        self.manager.create_docker_process(
            "exec", "-it", self.get_service_name("redroid-builder"),
            "sudo", "chown", "-R", self.get_config("DOCKER_USER"), "/src/"
        ).check_call()
