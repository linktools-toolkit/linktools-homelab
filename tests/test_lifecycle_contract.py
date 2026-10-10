#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline lifecycle contracts against the real current cntr implementation."""
import ast
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import yaml

from linktools.cntr import OperationContext, SourceContainer
from linktools.cntr.artifacts import bind_prepared_files
from linktools.cntr.lifecycle import HookPhase
from test_navigation_integrations import ROOT, load_container, make_manager


class SyntheticConfig:
    def __init__(self, **values):
        self.values = values

    def keys(self):
        return self.values.keys()

    def get(self, key, **kwargs):
        return self.values[key]

    def cast(self, value, **kwargs):
        return Path(value) if kwargs.get("type") == "path" else value


def isolated_container(relative, directory, **values):
    runtime = Mock()
    runtime.chmod.side_effect = lambda path, mode: Path(path).chmod(mode)
    manager = SimpleNamespace(
        logger=Mock(), env_config=SyntheticConfig(**values), runtime=runtime,
        app_path=Path(directory) / "app", app_data_path=Path(directory) / "data",
        data_path=Path(directory) / "state", containers={}, debug=False, user="synthetic-user",
        integration_snapshot={}, artifact_index=Mock(),
    )
    source = ROOT / relative
    container = load_container(source / "container.py")(manager, source, source.name)
    manager.containers[container.name] = container
    return container


class PreparedFileTests(unittest.TestCase):
    def test_config_hooks_prepare_immutable_files_and_preserve_active_mounts(self):
        cases = (
            ("3xx-proxy/310-frp-server", "frps.ini", dict(
                FRPS_BIND_PORT=7000, FRPS_BIND_TOKEN="synthetic-token",
                FRPS_VHOST_HTTP_PORT=80, FRPS_VHOST_HTTPS_PORT=443)),
            ("3xx-proxy/320-xray-server", "config.json", dict(
                XRAY_ID="synthetic-id", XRAY_WEBSOCKET_PATH="socket/",
                XRAY_GRPC_SERVICE_NAME="grpc/", XRAY_XHTTP_PATH="stream/")),
            ("3xx-proxy/340-shadowsocks-client", "config.json", dict(
                SHADOWSOCKS_SERVER_HOST="proxy.example.test", SHADOWSOCKS_SERVER_PORT=8388,
                SHADOWSOCKS_SERVER_PASSWORD="synthetic-password", SHADOWSOCKS_SERVER_METHOD="aes-256-gcm")),
            ("4xx-mobile/410-ws-scrcpy", "config.yaml", dict(WS_SCRCPY_PORT=8000)),
        )
        for relative, filename, values in cases:
            with self.subTest(container=relative), TemporaryDirectory() as directory:
                container = isolated_container(relative, directory, **values)
                legacy = container.get_app_path(filename, create_parent=True)
                legacy.write_text("active legacy input", encoding="utf-8")
                context = OperationContext(project_containers=[container], target_containers=[container])
                container.on_starting(context)
                container.on_check(context)
                prepared = context.file_path(container, filename)
                self.assertTrue(prepared.is_file())
                self.assertEqual(prepared.stat().st_mode & 0o777, 0o600)
                self.assertEqual(legacy.read_text(), "active legacy input")
                self.assertFalse(container.get_app_path("generated/current").exists())
                logical_source = container.get_app_path("generated/current", filename)
                model = {"services": {container.name: {"volumes": [{
                    "type": "bind", "source": str(logical_source), "target": "/config",
                }]}}}
                bound = bind_prepared_files(context, model, {})
                mount = bound["services"][container.name]["volumes"][0]
                self.assertEqual(mount["source"], str(prepared))
                self.assertIn('generated/current/' + filename,
                              (container.root_path / "compose.yml").read_text())
                repeat = OperationContext(project_containers=[container], target_containers=[container])
                container.on_starting(repeat)
                self.assertEqual(repeat.prepared_dirs, context.prepared_dirs)
                unchanged = bind_prepared_files(repeat, model, {container.name: yaml.safe_dump(bound)})
                self.assertEqual(unchanged, bound)
                container.manager.runtime.create_process.assert_not_called()
                container.manager.runtime.create_docker_process.assert_not_called()

    def test_ws_scrcpy_keeps_source_preparation_hook_and_snapshot_context(self):
        with TemporaryDirectory() as directory:
            container = isolated_container("4xx-mobile/410-ws-scrcpy", directory,
                                           WS_SCRCPY_URL="https://example.test/{tag}.zip",
                                           WS_SCRCPY_TAG="v1.2.3", WS_SCRCPY_PORT=8000)
            self.assertIsInstance(container, SourceContainer)
            hook = container.hooks.get(HookPhase.BEFORE_START, ("init_source_code", "ws-scrcpy"))
            self.assertIsNotNone(hook)
            self.assertEqual(hook.callback, container._prepare_source)
            self.assertEqual(container.get_docker_context_path().parts[-2:], ("current", "ws-scrcpy-1.2.3"))
            self.assertIsNone(container.get_build_revision("ws-scrcpy"))
            self.assertFalse(container.get_app_path().exists())

    def test_mihomo_only_refreshes_its_own_requested_service(self):
        container = make_manager().containers["mihomo"]
        with patch.dict(container.on_starting.__globals__, utils=Mock()) as namespace:
            for services, actions in ((frozenset(), ["pull"]), (frozenset({"other"}), ["up"])):
                container.on_starting(OperationContext(actions=actions, refresh_services=services))
                namespace["utils"].remove_file.assert_not_called()
            container.get_app_path = Mock(side_effect=lambda *parts: Path("/synthetic").joinpath(*parts))
            container.on_starting(OperationContext(actions=["up"], refresh_services=frozenset({"mihomo"})))
            self.assertEqual(namespace["utils"].remove_file.call_count, 2)

    def test_every_container_imports_and_has_no_removed_lifecycle_or_helpers(self):
        for path in ROOT.glob("*/*/container.py"):
            with self.subTest(container=path.parent.name):
                cls = load_container(path)
                self.assertNotIn("on_prepare", cls.__dict__)
                for node in ast.walk(ast.parse(path.read_text())):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        self.assertNotIn(node.module, ("linktools.cntr.urls", "linktools.cntr.integration",
                                                       "linktools.cntr.generation"))


class MulticaLifecycleTests(unittest.TestCase):
    def test_vscode_loading_is_lazy_and_composition_preserves_multica_injection(self):
        with TemporaryDirectory() as directory:
            multica = isolated_container("5xx-ai/521-multica", directory,
                                         MULTICA_APP_URL="https://multica.example.test",
                                         MULTICA_SERVER_URL="https://api.example.test",
                                         MULTICA_DAEMON_ID="synthetic-daemon", MULTICA_PAT="synthetic-pat")
            manager = multica.manager
            source = ROOT / "5xx-ai/500-vscode"
            vscode = load_container(source / "container.py")(manager, source, source.name)
            manager.containers["vscode"] = vscode
            multica.enable = True
            multica._write_pat = Mock()
            with patch.object(multica, "get_config", wraps=multica.get_config) as config:
                vscode.on_init()
                config.assert_not_called()
            # Repeated registration and Compose renders cannot accumulate hooks.
            vscode.on_init()
            for _ in range(2):
                compose = {"services": {"code-server": {"environment": [], "volumes": []}}}
                vscode.hooks.call(HookPhase.AFTER_COMPOSE_RENDER, compose)
                service = compose["services"]["code-server"]
                self.assertEqual(len(service["environment"]), 4)
                self.assertEqual(len(service["volumes"]), 3)
                self.assertIn("MULTICA_DAEMON_ID=synthetic-daemon", service["environment"])
                self.assertNotIn("synthetic-pat", str(compose))
                multica._write_pat.assert_not_called()
            self.assertFalse(multica.get_app_path().exists())
            vscode.hooks.call(HookPhase.BEFORE_START, OperationContext(target_containers=[vscode]))
            multica._write_pat.assert_called_once_with("synthetic-pat")

    def test_uninstalled_multica_never_resolves_its_config(self):
        with TemporaryDirectory() as directory:
            vscode = isolated_container("5xx-ai/500-vscode", directory)
            multica = SimpleNamespace(enable=False, configure_vscode=Mock())
            vscode.manager.containers["multica"] = multica
            vscode.on_init()
            compose = {"services": {"code-server": {"environment": [], "volumes": []}}}
            vscode.hooks.call(HookPhase.AFTER_COMPOSE_RENDER, compose)
            multica.configure_vscode.assert_not_called()


if __name__ == "__main__":
    unittest.main()
