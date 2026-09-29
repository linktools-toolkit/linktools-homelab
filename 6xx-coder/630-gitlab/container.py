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
import tempfile
import uuid
from typing import Iterable

from linktools.cli import subcommand, subcommand_argument
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
            GITLAB_TAG="latest",
            GITLAB_DOMAIN=self.get_nginx_domain(),
            GITLAB_SSH_PORT=ConfigField(cast=int, provider=PromptProvider(default=3001, cached=True)),
            GITLAB_ROOT_PASSWORD=ConfigField(provider=PromptProvider(  # gitlab默认root密码
                default="xxx123456xxxx", cached=True,
            )),
            GITLAB_DB_HOST="gitlab-postgres",
            GITLAB_DB_PORT="5432",
            GITLAB_DB_DATABASE="gitlab1",
            GITLAB_DB_USERNAME="gitlab2",
            GITLAB_DB_PASSWORD="gitlab3",
            GITLAB_REDIS_HOST="gitlab-redis",
            GITLAB_REDIS_PORT="6379",
            GITLAB_REDIS_PASSWORD="gitlab_redis_pass",
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("Gitlab", "git", "代码仓库管理", self.load_nginx_url(
                "GITLAB_DOMAIN",
                proxy_url="http://gitlab:8181",
                auth_enable=True,
                auth_extra={
                    "oidc_redirect_uris": ["{base_url}/users/auth/openid_connect/callback"]
                }
            )),
        ]

    @subcommand("fix", help="fix permissions")
    def on_exec_fix(self):
        self.manager.runtime.create_docker_process("exec", self.get_service_name("gitlab"), "update-permissions").check_call()
        self.manager.runtime.create_docker_process("restart", self.get_service_name("gitlab")).check_call()

    @subcommand("migrate-db", help="Export the old database and restore into a new PostgreSQL 18 directory")
    @subcommand_argument("--from-version", choices=["16", "17"], required=True,
                         help="PostgreSQL major version of the existing data")
    def on_exec_migrate_db(self, from_version):
        if self.get_config("GITLAB_DB_HOST") != "gitlab-postgres":
            raise ValueError("Only the bundled gitlab-postgres service is supported")
        source = self.get_app_path("postgres")
        target = self.get_app_path("postgres-18")
        if not source.is_dir() or target.exists():
            raise ValueError(f"Expected existing {source} and unused {target}")

        docker = self.manager.runtime.create_docker_process
        old_image, new_image = f"postgres:{from_version}-alpine", "postgres:18-alpine"
        docker("pull", old_image).check_call()
        docker("pull", new_image).check_call()
        # Check the data version through Docker, since its files may be owned by postgres.
        docker("run", "--rm", "--network", "none", "--entrypoint", "sh",
               "-v", f"{source}:/data:ro", old_image, "-ec",
               'test "$(cat /data/PG_VERSION)" = "$1"', "sh", from_version).check_call()

        backup = tempfile.mkdtemp(prefix="postgres-backup-", dir=self.get_app_path())
        target.mkdir()
        common = (
            "--rm", "--network", "none", "--entrypoint", "sh",
            "-v", f"{self.get_source_path('migrate-db.sh')}:/migrate-db.sh:ro",
            "-e", f"DB_USER={self.get_config('GITLAB_DB_USERNAME')}",
        )
        self.logger.info(f"Database dump: {backup}/cluster.sql; new data: {target}")
        docker("stop", "--timeout", "120", self.get_service_name("gitlab")).check_call()
        docker("stop", "--timeout", "120", self.get_service_name("gitlab-postgres")).check_call()
        docker("run", *common, "-v", f"{backup}:/backup",
               "-v", f"{source}:/var/lib/postgresql/data",
               old_image, "/migrate-db.sh", "dump").check_call()
        # A unique bootstrap role avoids colliding with roles restored by pg_dumpall.
        docker("run", *common, "-v", f"{backup}:/backup:ro",
               "-v", f"{target}:/var/lib/postgresql",
               "-e", f"POSTGRES_USER=migration_{uuid.uuid4().hex}",
               "-e", f"POSTGRES_PASSWORD={uuid.uuid4().hex}",
               "-e", "POSTGRES_DB=postgres",
               new_image, "/migrate-db.sh", "restore").check_call()
        self.logger.info(f"Migration complete. GitLab is stopped. Keep {source} as a backup, "
                         f"replace it with {target}, then run: ct-cntr up gitlab")

    # def on_started(self):
    #     self.manager.runtime.create_docker_process("exec", self.get_service_name("gitlab"), "chown", "-R", "git:git", "/var/opt/gitlab").check_call()
    #     self.manager.runtime.create_docker_process("exec", self.get_service_name("gitlab"), "chmod", "-R", "777", "/var/opt/gitlab").check_call()
    #     # self.manager.runtime.create_docker_process("exec", self.get_service_name("gitlab"), "update-permissions").check_call()
    #     # self.manager.runtime.create_docker_process("restart", self.get_service_name("gitlab")).check_call()
