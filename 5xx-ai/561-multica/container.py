#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import uuid
from typing import Iterable
from urllib.parse import urlparse

from linktools import utils
from linktools.cli import subcommand, subcommand_argument
from linktools.core import ConfigField, LazyProvider, PromptProvider
from linktools.decorator import cached_property
from linktools.cntr import BaseContainer, ContainerError, EventContext
from linktools.rich import choose, prompt


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["ai", "coder"]

    def _prompt_url(self, config, name):
        server = self.manager.containers.get("multica-server")
        if server is not None and server.enable:
            default = utils.make_url(
                config.get("NGINX_DEFAULT_SCHEME"),
                config.get("MULTICA_DOMAIN"),
                config.get("NGINX_DEFAULT_PORT"),
            )
            return prompt(name, default=default)
        return prompt(name)

    @cached_property
    def configs(self):
        return dict(
            MULTICA_CLIENT_TAG="latest",
            MULTICA_DAEMON_ID=ConfigField(provider=LazyProvider(lambda r: str(uuid.uuid4()), cached=True)),
            MULTICA_APP_URL=ConfigField(provider=LazyProvider(
                lambda r: self._prompt_url(r, "MULTICA_APP_URL"), cached=True,
            ), required=True),
            MULTICA_SERVER_URL=ConfigField(provider=LazyProvider(
                lambda r: self._prompt_url(r, "MULTICA_SERVER_URL"), cached=True,
            ), required=True),
            MULTICA_PAT=ConfigField(provider=PromptProvider(password=True, cached=True), required=True, secret=True),
        )

    def on_starting(self, context: "EventContext"):
        for key in ("MULTICA_APP_URL", "MULTICA_SERVER_URL"):
            value = self.get_config(key).strip()
            parsed = urlparse(value)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                raise ValueError(f"{key} must be an absolute HTTP(S) URL")

        pat = self.get_config("MULTICA_PAT").strip()
        if not pat:
            raise ValueError("MULTICA_PAT is required")

        secret_dir = self.get_app_path("secrets")
        secret_path = os.path.join(secret_dir, "multica_pat")
        os.makedirs(secret_dir, mode=0o700, exist_ok=True)
        os.chmod(secret_dir, 0o700)
        try:
            os.unlink(secret_path)
        except FileNotFoundError:
            pass
        with open(secret_path, "w", encoding="utf-8") as secret_file:
            secret_file.write(pat)
        os.chmod(secret_path, 0o400)
        self.manager.runtime.chown(
            secret_path,
            self.get_config("DOCKER_USER"),
            recursive=False,
        )

    @subcommand("show", help="show Multica IDs, or run a Multica command", prefix_chars=chr(1))
    @subcommand_argument("args", nargs="...", metavar="ARGS", help="optional Multica CLI arguments")
    def on_exec_show(self, args: "list[str]"):
        if not args:
            self._show_ids()
            return

        docker_args = ["exec", "-i"]
        if sys.stdin.isatty() and sys.stdout.isatty():
            docker_args.append("-t")
        self.manager.runtime.create_docker_process(
            *docker_args, self.get_service_name("multica"), "multica", *args,
        ).check_call()

    @subcommand("add-local", help="add a directory in this Multica container to a project")
    @subcommand_argument("local_path", metavar="PATH", help="absolute directory path inside the Multica container")
    @subcommand_argument("--workspace-id", help="workspace ID, name, or slug; prompts if omitted")
    @subcommand_argument("--project-id", help="project ID or title; prompts if omitted")
    @subcommand_argument("--execution-mode", choices=("worktree", "in_place"), default="worktree",
                         help="execution mode (default: worktree)")
    @subcommand_argument("--label", help="optional resource label")
    def on_exec_add_local(self, local_path: str, workspace_id: "str | None" = None,
                          project_id: "str | None" = None, execution_mode: str = "worktree",
                          label: "str | None" = None):
        if not os.path.isabs(local_path):
            raise ContainerError("PATH must be an absolute path inside the Multica container")

        service = self.get_service_name("multica")
        if self.manager.runtime.create_docker_process(
            "exec", service, "sh", "-c", 'test -d "$1"', "sh", local_path,
            capture_output=True,
        ).call() != 0:
            raise ContainerError(f"Directory is not available inside the Multica container: {local_path}")

        workspaces = self._multica_list("workspace", "list")
        workspace_id = self._select_multica_id("workspace", workspaces, workspace_id)
        projects = self._multica_list("project", "list", "--workspace-id", workspace_id)
        project_id = self._select_multica_id("project", projects, project_id)

        command = [
            "exec", service, "multica", "project", "resource", "add", project_id,
            "--type", "local_directory", "--local-path", local_path,
            "--daemon-id", self.get_config("MULTICA_DAEMON_ID"),
            "--execution-mode", execution_mode, "--workspace-id", workspace_id,
            "--output", "json",
        ]
        if label:
            command.extend(("--label", label))
        self.manager.runtime.create_docker_process(*command).check_call()

    def _multica_list(self, *args):
        process = self.manager.runtime.create_docker_process(
            "exec", self.get_service_name("multica"),
            "multica", *args, "--output", "json",
            capture_output=True,
        )
        rows = self.manager.structured_runner.execute_json(process)
        if isinstance(rows, dict):
            key = "resources" if args[:2] == ("project", "resource") else {
                "workspace": "workspaces",
                "project": "projects",
                "runtime": "runtimes",
                "agent": "agents",
                "skill": "skills",
                "squad": "squads",
                "label": "labels",
                "property": "properties",
                "autopilot": "autopilots",
            }.get(args[0])
            if key in rows:
                rows = rows[key]
            else:
                lists = [value for value in rows.values() if isinstance(value, list)]
                if len(lists) == 1:
                    rows = lists[0]
        if rows is None:
            return []
        if not isinstance(rows, list):
            raise ContainerError(f"Multica {' '.join(args)} did not return a list")
        return [row for row in rows if isinstance(row, dict)]

    @staticmethod
    def _multica_display_name(row):
        return next((row[key] for key in (
            "title", "name", "display_name", "slug", "url",
        ) if isinstance(row.get(key), str) and row[key]), "")

    def _select_multica_id(self, kind, rows, requested):
        requested = requested.strip() if requested else None
        choices = {}
        for row in rows:
            identifier = row.get("id")
            if not isinstance(identifier, str) or not identifier:
                continue
            if requested and not (
                identifier.startswith(requested)
                or any(isinstance(row.get(key), str) and row[key].casefold() == requested.casefold()
                       for key in ("title", "name", "slug"))
            ):
                continue
            choices[identifier] = f"{self._multica_display_name(row)} ({identifier})"
        if not choices:
            if requested:
                raise ContainerError(f"No {kind} matches {requested!r}")
            raise ContainerError(f"No {kind}s are available")
        if len(choices) == 1:
            return next(iter(choices))
        if not sys.stdin.isatty():
            raise ContainerError(f"Multiple {kind}s are available; pass --{kind}-id")
        return choose(f"Select {kind}", dict(sorted(choices.items(), key=lambda item: item[1].casefold())))

    @staticmethod
    def _print_ids(title, rows, indent="  "):
        print(f"{indent}{title}:")
        if not rows:
            print(f"{indent}  (none)")
        for row in sorted(rows, key=lambda item: Container._multica_display_name(item).casefold()):
            identifier = row.get("id")
            if not identifier:
                continue
            name = Container._multica_display_name(row)
            print(f"{indent}  {identifier}  {name}")

    def _show_ids(self):
        print(f"Daemon ID: {self.get_config('MULTICA_DAEMON_ID')}")
        workspaces = self._multica_list("workspace", "list")
        if not workspaces:
            print("Workspaces: (none)")
            return

        for workspace in sorted(workspaces, key=lambda item: self._multica_display_name(item).casefold()):
            workspace_id = workspace.get("id")
            if not workspace_id:
                continue
            name = self._multica_display_name(workspace)
            slug = workspace.get("slug")
            print(f"\nWorkspace: {workspace_id}  {name}" + (f" ({slug})" if slug and slug != name else ""))
            scope = ("--workspace-id", workspace_id)

            projects = self._multica_list("project", "list", *scope)
            self._print_ids("Projects", projects)
            for project in sorted(projects, key=lambda item: self._multica_display_name(item).casefold()):
                project_id = project.get("id")
                if not project_id:
                    continue
                resources = self._multica_list("project", "resource", "list", project_id, *scope)
                if not resources:
                    continue
                print(f"    Resources for {self._multica_display_name(project)}:")
                for resource in sorted(resources, key=lambda item: str(item.get("label") or item.get("id") or "").casefold()):
                    resource_id = resource.get("id")
                    if not resource_id:
                        continue
                    ref = resource.get("resource_ref")
                    ref = ref if isinstance(ref, dict) else {}
                    label = resource.get("label") or ref.get("local_path") or ref.get("url") or ""
                    detail = ref.get("local_path") or ref.get("url")
                    if detail and detail != label:
                        label = f"{label}  {detail}"
                    resource_type = resource.get("resource_type") or ""
                    mode = ref.get("execution_mode") or ""
                    daemon_id = ref.get("daemon_id") or ""
                    print(f"      {resource_id}  {resource_type}  {label}")
                    if mode or daemon_id:
                        print(f"        mode={mode or '-'}  daemon_id={daemon_id or '-'}")

            for title, command in (
                ("Runtimes", ("runtime", "list")),
                ("Agents", ("agent", "list")),
                ("Skills", ("skill", "list")),
                ("Squads", ("squad", "list")),
                ("Labels", ("label", "list")),
                ("Properties", ("property", "list")),
                ("Autopilots", ("autopilot", "list")),
            ):
                self._print_ids(title, self._multica_list(*command, *scope))
