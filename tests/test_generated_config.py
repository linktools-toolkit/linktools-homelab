#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Real template/file-hook contracts; no Docker daemon or user configuration."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from linktools.cntr import BaseContainer, OperationContext
from linktools.cntr.artifacts import prepared_hooks
from linktools.core import Config, ConfigSchema

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ("3xx-proxy/310-frp-server", "frps.ini", 0o600, "FRPS_BIND_TOKEN", "changed-token"),
    ("3xx-proxy/320-xray-server", "config.json", 0o644, "XRAY_ID", "changed-id"),
    ("3xx-proxy/340-shadowsocks-client", "config.json", 0o600, "SHADOWSOCKS_SERVER_PASSWORD", "changed-password"),
    ("4xx-mobile/410-ws-scrcpy", "config.yaml", 0o600, "WS_SCRCPY_PORT", 9000),
]
VALUES = dict(
    FRPS_TAG="latest", FRPS_BIND_PORT=7000, FRPS_BIND_TOKEN="test-token",
    FRPS_VHOST_HTTP_PORT=80, FRPS_VHOST_HTTPS_PORT=443,
    XRAY_TAG="latest", XRAY_ID="test-id", XRAY_WEBSOCKET_PATH="/ws",
    XRAY_GRPC_SERVICE_NAME="/grpc", XRAY_XHTTP_PATH="/xhttp",
    SHADOWSOCKS_CLIENT_TAG="latest", SHADOWSOCKS_CLIENT_PORT=1080,
    SHADOWSOCKS_SERVER_HOST="example.test", SHADOWSOCKS_SERVER_PORT=8388,
    SHADOWSOCKS_SERVER_PASSWORD="test-password", SHADOWSOCKS_SERVER_METHOD="aes-256-gcm",
    WS_SCRCPY_PORT=8000,
)


def make_container(folder, tmp_path, values=None):
    spec = importlib.util.spec_from_file_location("test_" + Path(folder).name.replace("-", "_"),
                                                ROOT / folder / "container.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    config = Config(None, ConfigSchema(), [])
    config.update_defaults(**dict(VALUES, **(values or {})))
    records = {}
    manager = SimpleNamespace(
        config=config, logger=SimpleNamespace(debug=lambda *args: None), debug=False,
        user="test", containers={}, app_path=tmp_path / "app", app_data_path=tmp_path / "data",
        container_host="/var/run/docker.sock", data_path=tmp_path,
        runtime=SimpleNamespace(chmod=os.chmod), integration_snapshot={},
        artifact_index=SimpleNamespace(record=lambda entries: records.update(entries)),
    )
    container = module.Container(manager, ROOT / folder, Path(folder).name)
    manager.containers[container.name] = container
    return container, records


@pytest.mark.parametrize("folder,filename,mode,key,new_value", CASES)
def test_compose_captures_exact_immutable_inputs_before_start(tmp_path, monkeypatch, folder, filename, mode, key, new_value):
    container, records = make_container(folder, tmp_path)
    model = yaml.safe_load(container.render_template(container.get_source_path("compose.yml")))
    path = container.config_path
    volumes = [mount for service in model["services"].values() for mount in service.get("volumes", [])]
    assert any(mount.split(":", 1)[0] == str(path / filename) for mount in volumes)
    assert not path.exists()
    assert not records
    assert len(prepared_hooks(container)) == 1
    assert container.config_path is path

    # The configuration belongs to this render, even if a provider changes later.
    container.config.update_defaults(**{key: new_value})
    def unexpected(*args, **kwargs):
        raise AssertionError("start/check must not resolve or render configuration again")
    monkeypatch.setattr(container, "render_template", unexpected)
    monkeypatch.setattr(container, "get_config", unexpected)
    context = OperationContext(project_containers=[container], target_containers=[])
    prepared_hooks(container)[0].callback(context)
    container.on_check(context)

    content = (path / filename).read_text(encoding="utf-8")
    payload = json.dumps([mode, None, 0o755, [(filename, content)]], ensure_ascii=True, separators=(",", ":"))
    assert path.name == hashlib.sha256(payload.encode("utf-8")).hexdigest()
    assert context.file_path(container, filename) == path / filename
    assert (path / filename).stat().st_mode & 0o777 == mode
    assert not (path.parent / "current").exists()
    tree = os.path.relpath(path, container.manager.data_path)
    file_records = {key: entry for key, entry in records.items() if entry["kind"] == "generated-config"}
    tree_records = {key: entry for key, entry in records.items() if entry["kind"] == "generated-config-tree"}
    assert len(records) == 2
    assert file_records == {
        os.path.relpath(path / filename, container.manager.data_path): {
            "kind": "generated-config", "container": container.name,
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "tree": tree, "producers": [],
        },
    }
    assert tree_records == {
        tree: {
            "kind": "generated-config-tree", "container": container.name,
            "tree": tree, "producers": [],
        },
    }

    next_container, _ = make_container(folder, tmp_path, {key: new_value})
    assert next_container.config_path != path
    assert not next_container.config_path.exists()


@pytest.mark.parametrize("folder,filename,mode,key,new_value", CASES)
def test_config_path_uses_inherited_prepare_files(tmp_path, monkeypatch, folder, filename, mode, key, new_value):
    calls = []
    prepared_path = tmp_path / "prepared"

    def prepare_files(self, files, *, revision=None, mode=0o600, group=None):
        calls.append((self, files, revision, mode, group))
        return prepared_path

    monkeypatch.setattr(BaseContainer, "prepare_files", prepare_files)
    container, records = make_container(folder, tmp_path)
    assert container.config_path is prepared_path
    assert container.config_path is prepared_path
    assert len(calls) == 1
    owner, files, revision, actual_mode, group = calls[0]
    assert owner is container
    assert set(files) == {filename}
    assert isinstance(files[filename], str) and files[filename]
    assert revision is None
    assert actual_mode == mode
    assert group is None
    assert not prepared_hooks(container)
    assert not records
    assert not prepared_path.exists()


@pytest.mark.parametrize("folder,filename,mode,key,new_value", CASES)
def test_unrendered_consumer_does_not_resolve_config(tmp_path, monkeypatch, folder, filename, mode, key, new_value):
    container, records = make_container(folder, tmp_path)
    def unexpected(*args, **kwargs):
        raise AssertionError("unrendered consumer must stay lazy")
    monkeypatch.setattr(container, "get_config", unexpected)
    monkeypatch.setattr(container, "render_template", unexpected)
    assert not prepared_hooks(container)
    assert "config_path" not in container.__dict__
    assert not records
    assert not container.get_app_path("generated").exists()


@pytest.mark.parametrize("installed", [False, True])
def test_partial_project_resolves_only_installed_consumers(tmp_path, monkeypatch, installed):
    from linktools.cntr import BaseContainer, ContainerManager
    from linktools.cntr.artifacts import collect_candidates
    from linktools.core import Environ

    for key, value in (("LINKTOOLS_PATH", tmp_path), ("LINKTOOLS_DATA_PATH", tmp_path / "data"),
                       ("LINKTOOLS_TEMP_PATH", tmp_path / "temp")):
        monkeypatch.setenv(key, str(value))
    manager = ContainerManager(Environ(), name="generated-test")
    app_root = tmp_path / "fixture"
    app_root.mkdir()
    (app_root / "compose.yml").write_text("services:\n  app:\n    image: example:test\n", encoding="utf-8")
    app = BaseContainer(manager, app_root, "app")
    nginx = BaseContainer(manager, tmp_path / "nginx", "nginx")
    consumers = []
    for folder, *_ in CASES:
        container, _ = make_container(folder, tmp_path)
        container.manager = manager
        container.logger = manager.logger
        consumers.append(container)
    manager.__dict__["containers"] = {c.name: c for c in [app, nginx] + consumers}
    for key, value in dict(VALUES, DOCKER_APP_PATH=str(tmp_path / "apps"),
                           DOCKER_USER="root", WS_SCRCPY_TAG="master").items():
        manager.config.set(key, value)
    manager.installed_state.add("app", *([c.name for c in consumers] if installed else []))
    selection = manager.compose_operations.select(["app"])
    assert selection.target_containers == (app,)
    assert all("config_path" not in c.__dict__ for c in consumers)
    candidates = collect_candidates(manager, selection.project_containers)
    assert candidates
    for consumer in consumers:
        assert ("config_path" in consumer.__dict__) is installed
        assert bool(prepared_hooks(consumer)) is installed
        assert not consumer.get_app_path("generated").exists()
