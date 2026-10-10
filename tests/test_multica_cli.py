import argparse
import unittest
from unittest.mock import Mock, patch

from linktools.cli._command import SubCommandMixin
from linktools.cntr import ContainerError
from test_navigation_integrations import ROOT, load_container


SOURCE = ROOT / "5xx-ai/521-multica"
Container = load_container(SOURCE / "container.py")


class MulticaCliTests(unittest.TestCase):
    def setUp(self):
        self.manager = Mock(project_name="test")
        self.container = Container(self.manager, SOURCE, "multica")
        self.confirm = Mock(return_value=True)
        confirmation = patch.dict(self.container.on_exec_remove_resource.__globals__, confirm=self.confirm)
        confirmation.start()
        self.addCleanup(confirmation.stop)
        output = patch("builtins.print")
        self.print = output.start()
        self.addCleanup(output.stop)
        self.container.get_config = Mock(return_value="daemon-current")
        self.container._multica_list = Mock(side_effect=lambda *args: (
            [{"id": "ws-1", "name": "team"}] if args[0] == "workspace" else
            self.resources if args[:2] == ("project", "resource") else
            [{"id": "project-1", "title": "backend"}]
        ))
        self.resources = [
            {"id": "local-1", "resource_type": "local_directory", "label": "local",
             "resource_ref": {"local_path": "/workspace/Repo", "daemon_id": "daemon-current"}},
            {"id": "github-1", "resource_type": "github_repo", "label": "remote",
             "resource_ref": {"url": "https://github.com/owner/repo"}},
        ]

    def command(self):
        return self.manager.runtime.create_docker_process.call_args.args

    def test_add_github_passes_scope_ref_and_label_as_separate_arguments(self):
        self.container.on_exec_add_github("https://github.com/owner/repo", "team", "backend",
                                          ref="release/test", label="label $(untouched)")
        self.assertEqual(self.command(), (
            "exec", "test-code-server", "/workspace/.local/bin/multica",
            "project", "resource", "add", "project-1", "--type", "github_repo",
            "--url", "https://github.com/owner/repo", "--workspace-id", "ws-1",
            "--output", "json", "--ref", "release/test", "--label", "label $(untouched)",
        ))

    def test_remove_local_selects_by_path_and_only_detaches(self):
        self.container.on_exec_remove_resource(resource_id="/workspace/Repo")
        self.assertEqual(self.command(), (
            "exec", "test-code-server", "/workspace/.local/bin/multica",
            "project", "resource", "remove", "project-1", "local-1",
            "--workspace-id", "ws-1", "--output", "json",
        ))

    def test_remove_github_selects_by_url(self):
        self.container.on_exec_remove_resource(resource_id="https://github.com/owner/repo")
        self.assertIn("github-1", self.command())

    def test_confirmation_defaults_to_cancel_and_shows_selected_resource(self):
        self.container.on_exec_remove_resource(resource_id="github-1")
        self.confirm.assert_called_once_with("Detach this resource from the project?", default=False)
        output = "\n".join(call.args[0] for call in self.print.call_args_list)
        for value in ("ws-1", "project-1", "github-1", "github_repo", "https://github.com/owner/repo", "whole project"):
            self.assertIn(value, output)

    def test_declined_confirmation_prevents_removal_in_all_selection_modes(self):
        self.confirm.return_value = False
        self.resources = [self.resources[0]]
        for args in ({}, {"resource_id": "local-1"}, {"resource_id": "local-1", "all_daemons": True}):
            with self.subTest(args=args):
                self.confirm.reset_mock()
                self.container.on_exec_remove_resource(**args)
                self.confirm.assert_called_once()
                self.manager.runtime.create_docker_process.assert_not_called()

    def test_confirmation_eof_prevents_removal(self):
        self.confirm.side_effect = EOFError
        self.container.on_exec_remove_resource(resource_id="local-1")
        self.manager.runtime.create_docker_process.assert_not_called()

    def test_unknown_resource_and_wrong_case_are_rejected(self):
        for resource in ("unknown", "/workspace/repo"):
            with self.subTest(resource=resource), self.assertRaises(ContainerError):
                self.container.on_exec_remove_resource(resource_id=resource)
        self.manager.runtime.create_docker_process.assert_not_called()

    def test_ambiguous_removal_in_noninteractive_mode_does_not_mutate(self):
        self.resources.append({"id": "local-2", "resource_type": "local_directory",
                               "resource_ref": {"local_path": "/workspace/other", "daemon_id": "daemon-current"}})
        with patch("sys.stdin.isatty", return_value=False), self.assertRaises(ContainerError):
            self.container.on_exec_remove_resource()
        self.manager.runtime.create_docker_process.assert_not_called()

    def test_other_daemon_and_unassigned_local_resources_are_filtered(self):
        self.resources = [
            {"id": "owned", "resource_type": "local_directory", "resource_ref": {"daemon_id": "daemon-current"}},
            {"id": "foreign", "resource_type": "local_directory", "resource_ref": {"daemon_id": "daemon-other"}},
            {"id": "unassigned", "resource_type": "local_directory", "resource_ref": {}},
        ]
        self.container.on_exec_remove_resource(resource_id="owned")
        self.assertIn("owned", self.command())
        self.manager.runtime.create_docker_process.reset_mock()
        for identifier in ("foreign", "unassigned"):
            with self.assertRaises(ContainerError):
                self.container.on_exec_remove_resource(resource_id=identifier)
        self.manager.runtime.create_docker_process.assert_not_called()
        self.container.on_exec_remove_resource(resource_id="foreign", all_daemons=True)
        self.assertIn("foreign", self.command())

    def test_shared_github_resource_is_available_without_all_daemons(self):
        self.resources = [self.resources[1]]
        self.container.on_exec_remove_resource(resource_id="github-1")
        self.assertIn("github-1", self.command())

    def test_mixed_resource_types_require_selection_and_show_type(self):
        with patch("sys.stdin.isatty", return_value=False), self.assertRaises(ContainerError):
            self.container.on_exec_remove_resource()
        self.manager.runtime.create_docker_process.assert_not_called()
        with patch("sys.stdin.isatty", return_value=True), patch.dict(
            self.container._select_multica_id.__globals__,
            choose=Mock(return_value="github-1"),
        ):
            self.container.on_exec_remove_resource()
            choices = self.container._select_multica_id.__globals__["choose"].call_args.args[1]
            self.assertIn("[local_directory]", choices["local-1"])
            self.assertIn("[github_repo]", choices["github-1"])
        self.assertIn("github-1", self.command())

    def test_new_commands_are_registered_and_accept_arguments(self):
        commands = {c.name: c for c in SubCommandMixin().walk_subcommands(self.container)}
        self.assertNotIn("remove", commands)
        self.assertNotIn("remove-local", commands)
        self.assertNotIn("remove-github", commands)
        for name in ("add-github", "remove-resource"):
            parser = argparse.ArgumentParser()
            commands[name].create_parser(parser.add_subparsers().add_parser)
            arguments = [name, "--workspace-id", "team", "--project-id", "backend"]
            arguments += ["https://github.com/owner/repo", "--ref", "main"] if name == "add-github" else ["--resource-id", "res-1"]
            parsed = parser.parse_args(arguments)
            self.assertEqual(parsed.workspace_id, "team")
            self.assertEqual(parsed.project_id, "backend")
            if name != "add-github":
                self.assertFalse(parsed.all_daemons)
                self.assertTrue(parser.parse_args(arguments + ["--all-daemons"]).all_daemons)


if __name__ == "__main__":
    unittest.main()
