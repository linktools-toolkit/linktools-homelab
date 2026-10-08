#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Homelab declarations and mocked rendering, without Docker or live services."""
import ast
from collections import Counter
from functools import lru_cache
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from jinja2 import Environment
import yaml

import linktools.cntr
from linktools.cntr import ContainerManager, ExposeLink
from linktools.cntr.generation import FlareGeneration


ROOT = Path(__file__).resolve().parents[1]


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
        if self.declaring and key != "NGINX_AUTH_ENABLE":
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
        name: SimpleNamespace(name=name, integrations={})
        for name in ("nginx", "flare", "authelia")
    }
    for path in declaration_paths():
        container = load_container(path)(manager, path.parent, path.parent.name)
        containers[container.name] = container
    manager.__dict__["containers"] = containers
    manager.__dict__["installed_state"] = SimpleNamespace(
        get=lambda resolve: tuple(containers.values()),
    )
    # Collect declarations and site views while every config read except auth
    # policy switches fails. URL resolution must happen only during rendering.
    manager.integration_snapshot
    manager.nginx_sites
    manager.env_config.declaring = False
    return manager


def render_flare(manager):
    path = Path(linktools.cntr.__file__).parent.parent / "assets/containers/120-flare/container.py"
    flare = load_container(path)(manager, path.parent, "flare")
    return {name: yaml.safe_load(text) for name, text in FlareGeneration(flare).render("test").items()}


def render_compose(container, auth):
    environment = Environment()
    environment.filters.update(mkdir=lambda path: path, chown=lambda path: path)
    context = dict(
        container=container, manager=container.manager,
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
        self.assertEqual(len(entries), 65)
        self.assertEqual(len({producer.name for producer, _, _ in entries}), 25)
        self.assertEqual(len(manager.nginx_sites), 31)
        self.assertEqual(len({(producer.name, key) for producer, key, _ in entries}), 65)
        self.assertTrue(all(isinstance(link, ExposeLink) for _, _, link in entries))
        self.assertEqual(set(manager.env_config.reads), {"NGINX_AUTH_ENABLE"})
        self.assertEqual(Counter(link.category.name for _, _, link in entries), {
            "public": 29, "private": 9, "container": 22, "other": 5,
        })
        for path in declaration_paths():
            self.assertNotIn("exposes", load_container(path).__dict__)

    def test_it_tools_preserves_all_links_and_bookmark_order(self):
        manager = make_manager()
        links = manager.containers["it-tools"].integrations["flare"]
        self.assertEqual(list(links), [
            "regex_tester", "regex_memo", "json_prettify", "dns_lookup", "icons", "direct", "public",
        ])
        self.assertEqual([link.url for link in links.values()], [
            "https://it-tools.example.test:8443/regex-tester",
            "https://it-tools.example.test:8443/regex-memo",
            "https://it-tools.example.test:8443/json-prettify",
            "https://tool.chinaz.com/dns/", "https://materialdesignicons.com/",
            "http://host.example.test:9000", "https://it-tools.example.test:8443",
        ])

    def test_direct_only_and_proxy_only_services_remain_independent(self):
        manager = make_manager()
        self.assertEqual(list(manager.containers["ws-scrcpy"].integrations), ["flare"])
        self.assertEqual(list(manager.containers["xray-server"].integrations), ["nginx"])
        self.assertEqual(manager.containers["ws-scrcpy"].integrations["flare"]["direct"].url,
                         "http://host.example.test:9000")

    def test_flare_renders_all_links_with_preserved_categories_and_order(self):
        manager = make_manager()
        entries = sorted(manager.iter_integrations("flare"), key=lambda item: item[0].order)
        expected_apps = []
        expected_bookmarks = {}
        for _, _, link in entries:
            if link.category.name == "public":
                expected_apps.append(dict(name=link.name, desc=link.desc, icon=link.icon, link=link.url))
            else:
                expected_bookmarks.setdefault(link.category.name, []).append(dict(
                    category=link.category.name, name=link.name, icon=link.icon, link=link.url,
                ))
        rendered = render_flare(manager)
        self.assertEqual(rendered["apps.yml"]["links"], expected_apps)
        self.assertEqual(rendered["bookmarks.yml"]["links"], [
            link for links in expected_bookmarks.values() for link in links
        ])
        self.assertEqual(len(expected_apps) + len(rendered["bookmarks.yml"]["links"]), 65)

    def test_disabled_links_are_omitted_but_external_bookmarks_survive(self):
        manager = make_manager(IT_TOOLS_DOMAIN="", IT_TOOLS_PORT=0)
        rendered = render_flare(manager)
        self.assertNotIn("IT Tools", [link["name"] for link in rendered["apps.yml"]["links"]])
        links = rendered["bookmarks.yml"]["links"]
        self.assertFalse(any(link["name"] in ("IT Tools", "正则表达式测试", "正则表达式手册", "在线json解析") for link in links))
        self.assertEqual([link["link"] for link in links if link["category"] == "other"], [
            "https://tool.chinaz.com/dns/", "https://materialdesignicons.com/",
        ])

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
