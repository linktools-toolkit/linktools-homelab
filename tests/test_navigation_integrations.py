#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Homelab declarations and mocked rendering, without Docker or live services."""
import ast
from collections import Counter
from functools import lru_cache
import json
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from jinja2 import Environment
import yaml

import linktools.cntr
from linktools.cntr import ContainerManager, Integration
from linktools.cntr import ext as urls
from linktools.cntr.repo.requirements import ensure_requirement
from linktools.capabilities.cntr import __cap_cntr__


ROOT = Path(__file__).resolve().parents[1]
ensure_requirement(json.loads((ROOT / ".linktools.json").read_text()), "linktools-cntr", __cap_cntr__.version)


@lru_cache(maxsize=None)
def load_container(path):
    return runpy.run_path(str(path), run_name="homelab_navigation_" + path.parent.name)["Container"]


@lru_cache(maxsize=1)
def declaration_paths():
    return tuple(path for path in sorted(ROOT.glob("*/*/container.py")) if any(
        isinstance(node, ast.FunctionDef) and node.name == "integrations"
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
    ))


class FakeConfig:
    def __init__(self, **values):
        self.declaring = True
        self.reads = []
        self.values = dict(
            HOST="host.example.test", NGINX_HTTPS_ENABLE=True,
            NGINX_AUTH_ENABLE=False, NGINX_WAF_ENABLE=False,
            NGINX_HTTP_PORT=8080, NGINX_HTTPS_PORT=8443,
            NGINX_WILDCARD_DOMAIN=True, MIHOMO_SECRET="test-secret",
        )
        self.values.update(values)

    def get(self, key, **kwargs):
        self.reads.append(key)
        if self.declaring:
            raise AssertionError("Declaration eagerly read " + key)
        if key in self.values:
            return self.values[key]
        if key.endswith("_DOMAIN"):
            return key[:-7].lower().replace("_", "-") + ".example.test"
        if key.endswith("_LOCAL_URL"):
            return "http://" + key[:-10].lower().replace("_", "-") + ".local.test"
        if key.endswith("_PORT"):
            return 9000
        raise AssertionError("Unexpected configuration read: " + key)


def make_manager(**values):
    manager = object.__new__(ContainerManager)
    manager.__dict__["logger"] = Mock()
    manager.env_config = FakeConfig(**values)
    containers = {
        name: SimpleNamespace(name=name, integrations=(), enable=True)
        for name in ("nginx", "flare", "authelia", "safeline")
    }
    for path in declaration_paths():
        container = load_container(path)(manager, path.parent, path.parent.name)
        containers[container.name] = container
    manager.__dict__["containers"] = containers
    manager.__dict__["installed_state"] = SimpleNamespace(
        get=lambda resolve: tuple(containers.values()),
    )
    # Collect declarations and site views while every configuration read fails. URL resolution must happen only during rendering.
    manager.integration_snapshot
    manager.nginx_sites
    manager.env_config.declaring = False
    return manager


def render_flare(manager):
    path = Path(linktools.cntr.__file__).parent.parent / "assets/containers/120-flare/container.py"
    flare = load_container(path)(manager, path.parent, "flare")
    return {name: yaml.safe_load(text) for name, text in flare._navigation_files().items()}


def render_compose(container, auth):
    environment = Environment()
    environment.filters.update(mkdir=lambda path: path, chown=lambda path: path)
    context = dict(
        container=container, manager=container.manager, urls=urls,
        APP_PATH=Path("/mock/app"), APP_DATA_PATH=Path("/mock/data"),
        SOURCE_PATH=container.root_path, NGINX_AUTH_ENABLE=auth,
    )
    # Only plain placeholders are needed for unrelated Compose configuration.
    context.update({key: "test-value" for key in container.configs})
    context["LITELLM_PORT"] = 9000
    return environment.from_string(
        (container.root_path / "compose.yml").read_text(encoding="utf-8"),
    ).render(context)


class NavigationIntegrationTests(unittest.TestCase):
    def test_all_links_are_unique_ordered_declarations_without_eager_secrets(self):
        manager = make_manager()
        entries = list(manager.iter_integrations("flare"))
        attached = [(producer, key, site.expose)
                    for producer, key, site in manager.iter_integrations("nginx")
                    if site.expose is not None]
        self.assertEqual(len(entries), 41)
        self.assertEqual(len(attached), 24)
        self.assertEqual(len({producer.name for producer, _, _ in entries + attached}), 25)
        self.assertEqual(len(manager.nginx_sites), 31)
        self.assertTrue(all(key is None for _, key, _ in entries))
        self.assertEqual(len({(producer.name, key) for producer, key, _ in attached}), 24)
        self.assertTrue(all(isinstance(link, Integration) for _, _, link in entries + attached))
        self.assertEqual(manager.env_config.reads, [])
        self.assertEqual([producer.name for producer, _, link in entries
                          if link.display_category.name == "public"], [
            "mihomo", "litellm", "mcp-playwright", "mcp-push", "pypiserver",
        ])
        rendered = render_flare(manager)
        apps = rendered["apps.yml"]["links"]
        bookmarks = rendered["bookmarks.yml"]["links"]
        self.assertEqual(len(apps) + len(bookmarks), 65)
        self.assertEqual(Counter(["public"] * len(apps) + [link["category"] for link in bookmarks]), {
            "public": 29, "private": 9, "container": 22, "other": 5,
        })
        for container in manager.containers.values():
            self.assertIsInstance(container.integrations, (list, tuple))
        for path in declaration_paths():
            self.assertNotIn("exposes", load_container(path).__dict__)

    def test_it_tools_preserves_all_links_and_bookmark_order(self):
        manager = make_manager()
        links = [link for link in manager.containers["it-tools"].integrations if link.consumer == "flare"]
        self.assertEqual([link.name for link in links], [
            "正则表达式测试", "正则表达式手册", "在线json解析", "DNS查询", "图标下载", "IT Tools",
        ])
        self.assertEqual([link.url for link in links], [
            "https://it-tools.example.test:8443/regex-tester",
            "https://it-tools.example.test:8443/regex-memo",
            "https://it-tools.example.test:8443/json-prettify",
            "https://tool.chinaz.com/dns/", "https://materialdesignicons.com/",
            "http://host.example.test:9000",
        ])

    def test_direct_only_and_proxy_only_services_remain_independent(self):
        manager = make_manager()
        self.assertEqual([item.consumer for item in manager.containers["ws-scrcpy"].integrations], ["flare"])
        self.assertEqual([item.consumer for item in manager.containers["xray-server"].integrations], ["nginx"])
        self.assertEqual(manager.containers["ws-scrcpy"].integrations[0].url,
                         "http://host.example.test:9000")

    def test_flare_renders_all_links_with_preserved_categories_and_order(self):
        manager = make_manager()
        # Frozen before moving the 24 root links onto their nginx sites. Compare
        # complete generated files so names, URLs, metadata and order cannot drift.
        expected = json.loads((ROOT / "tests/fixtures/navigation.json").read_text(encoding="utf-8"))
        self.assertEqual(render_flare(manager), expected)

    def test_attached_links_follow_http_and_disabled_site_policy(self):
        manager = make_manager(NGINX_HTTPS_ENABLE=False, PVE_LOCAL_URL="", AIONUI_DOMAIN="")
        apps = render_flare(manager)["apps.yml"]["links"]
        self.assertEqual(len(apps), 27)
        self.assertNotIn("Proxmox", [link["name"] for link in apps])
        self.assertNotIn("AionUI", [link["name"] for link in apps])
        self.assertEqual(next(link["link"] for link in apps if link["name"] == "IT Tools"),
                         "http://it-tools.example.test:8080")

    def test_disabled_links_are_omitted_but_external_bookmarks_survive(self):
        manager = make_manager(IT_TOOLS_DOMAIN="", IT_TOOLS_PORT=0)
        rendered = render_flare(manager)
        self.assertNotIn("IT Tools", [link["name"] for link in rendered["apps.yml"]["links"]])
        links = rendered["bookmarks.yml"]["links"]
        self.assertFalse(any(link["name"] in ("IT Tools", "正则表达式测试", "正则表达式手册", "在线json解析") for link in links))
        self.assertEqual([link["link"] for link in links if link["category"] == "other"], [
            "https://tool.chinaz.com/dns/", "https://materialdesignicons.com/",
        ])

    def test_vscode_proxy_url_keeps_literal_placeholder_and_site_policy(self):
        for https, wildcard, expected in (
            (True, True, "https://{{port}}.vscode.example.test:8443"),
            (False, True, "http://{{port}}.vscode.example.test:8080"),
            (True, False, ""),
        ):
            with self.subTest(https=https, wildcard=wildcard):
                manager = make_manager(NGINX_HTTPS_ENABLE=https, NGINX_WILDCARD_DOMAIN=wildcard)
                self.assertEqual(str(manager.containers["vscode"].proxy_url), expected)

    def test_no_removed_container_helpers_remain(self):
        removed = {"expose_public", "expose_private", "expose_container", "expose_other",
                   "load_nginx_url", "load_port_url", "load_config_url", "load_exist_nginx_url", "get_nginx_domain", "on_prepare"}
        for path in ROOT.glob("*/*/container.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                    if node.value.id in ("self", "container"):
                        self.assertNotIn(node.attr, removed, str(path))

    def test_gitlab_and_litellm_use_site_policy_in_compose(self):
        for https, port, auth in ((False, 8080, False), (True, 8443, False), (True, 8443, True)):
            with self.subTest(https=https, auth=auth):
                manager = make_manager(NGINX_HTTPS_ENABLE=https, NGINX_AUTH_ENABLE=auth)
                manager.containers["authelia"].oidc_client = dict(
                    issuer_url="https://auth.example.test", client_id="test-client", client_secret="test-secret",
                )
                gitlab = render_compose(manager.containers["gitlab"], auth)
                litellm = render_compose(manager.containers["litellm"], auth)
                scheme = "https" if https else "http"
                gitlab_url = "%s://gitlab.example.test:%s" % (scheme, port)
                litellm_url = "%s://litellm.example.test:%s" % (scheme, port)
                self.assertIn("external_url '%s'" % gitlab_url, gitlab)
                self.assertIn("PROXY_BASE_URL=%s" % litellm_url, litellm)
                self.assertEqual("redirect_uri:" in gitlab, auth)
                if auth:
                    self.assertIn('redirect_uri: "%s/users/auth/openid_connect/callback"' % gitlab_url, gitlab)
                    self.assertIn("GENERIC_CLIENT_ID=test-client", litellm)
                yaml.safe_load(gitlab)
                yaml.safe_load(litellm)


if __name__ == "__main__":
    unittest.main()
