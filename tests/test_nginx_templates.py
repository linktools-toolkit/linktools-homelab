#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Native-template render contracts; never starts nginx, Docker, or a service."""
import json
from pathlib import Path
import re
import unittest

from jinja2 import Environment

import linktools.cntr
from linktools.cntr.generation import NginxGeneration
from test_navigation_integrations import ROOT, load_container, make_manager


VALUES = dict(
    COMPOSE_PROJECT_NAME="fixture", NGINX_ROOT_DOMAIN="example.test", NGINX_INDEX_URL="https://example.test",
    SAFELINE_SUBNET_PREFIX="172.30.0", AIONUI_TOKEN="synthetic-aionui-token",
    PRIMARY_GATEWAY_AUTHORIZATION="synthetic-primary-token",
    BYPASS_GATEWAY_AUTHORIZATION="synthetic-bypass-token",
    MCP_PLAYWRIGHT_TOKEN="synthetic-playwright-token", SUBLINK_API_KEY="synthetic-sublink-key",
    XRAY_WEBSOCKET_PATH="/i/am/websocket", XRAY_GRPC_SERVICE_NAME="/i/am/grpc",
    XRAY_XHTTP_PATH="/i/am/xhttp",
    FNOS_LOCAL_URL="http://10.10.10.1:5666", FNOS_DAV_LOCAL_URL="http://10.10.10.1:5005",
)


def render_nginx(**values):
    config = dict(VALUES)
    config.update(values)
    manager = make_manager(**config)
    path = Path(linktools.cntr.__file__).parent.parent / "assets/containers/100-nginx/container.py"
    nginx = load_container(path)(manager, path.parent, "nginx")
    files = NginxGeneration(nginx).render("fixture")
    bodies = {key: files["sites/" + site.file_id + "/business.conf"]
              for key, site in manager.nginx_sites.items() if site.enabled and site.template}
    return manager, files, bodies


class NativeTemplateTests(unittest.TestCase):
    def test_all_twelve_templates_render_with_complete_headers_and_runtime_dns(self):
        for auth in (False, True):
            for waf in (False, True):
                with self.subTest(auth=auth, waf=waf):
                    _, files, bodies = render_nginx(NGINX_AUTH_ENABLE=auth, NGINX_WAF_ENABLE=waf)
                    self.assertEqual(len(bodies), 12)
                    for key, body in bodies.items():
                        self.assertNotIn("/etc/nginx/conf.d/snippets/", body, key)
                        # fnOS's numeric local targets retain native URI semantics.
                        if key != ("fnos", "web"):
                            self.assertNotRegex(body, r"(?:proxy|grpc)_pass\s+(?:https?|grpc)://")
                        self.assertIn('"X-Forwarded-Proto" "$cntr_scheme"', body, key)
                        self.assertIn('"X-Forwarded-For" "$cntr_client_ip"', body, key)
                    self.assertFalse(any("snippet" in name for name in files))
                    servers = [body for name, body in files.items()
                               if name.startswith("sites/") and name.count("/") == 1]
                    self.assertTrue(all("resolver 127.0.0.11 valid=5s;" in body for body in servers))

    def test_uri_replacement_capture_and_query_contracts(self):
        _, _, bodies = render_nginx()
        nextcloud = bodies[("nextcloud", "web")]
        self.assertIn("location ^~ /onlyoffice/", nextcloud)
        self.assertIn("rewrite ^/onlyoffice/(.*)$ /$1 break;", nextcloud)
        self.assertLess(nextcloud.index("set $onlyoffice_backend"), nextcloud.index("rewrite ^/onlyoffice/"))
        self.assertIn("proxy_pass $onlyoffice_backend;", nextcloud)
        self.assertIn('"X-Forwarded-Host" "$cntr_host/onlyoffice"', nextcloud)
        self.assertIn("return 301 $cntr_scheme://$cntr_host/remote.php/dav/", nextcloud)
        pypi = bodies[("pypiserver", "web")]
        self.assertIn("rewrite ^/pypi(.*)$ /$1 break;", pypi)
        self.assertLess(pypi.index("set $pypi_backend"), pypi.index("rewrite ^/pypi"))
        self.assertIn('set $pypi_target "http://pypi-server:8080/$1";', pypi)
        self.assertIn("location ~ ((?:simple|packages).*)", pypi)
        self.assertNotIn("$is_args", pypi)
        vscode = bodies[("vscode", "proxy")]
        self.assertIn("http://code-server:8080/proxy/$proxy_port$request_uri", vscode)
        self.assertIn('"X-Forwarded-Prefix" "/proxy/$proxy_port"', vscode)

    def test_webdav_rewrite_runs_after_destination_initialization(self):
        _, _, bodies = render_nginx()
        body = bodies[("fnos", "web")]
        rewrite = body.index("rewrite ^/dav/(.*)$ /$1 break;")
        self.assertLess(body.index("set $dav_destination $1;"), rewrite)
        self.assertIn('"Destination" "$dav_destination"', body)
        self.assertIn('"Accept-Encoding" ""', body)
        self.assertIn("proxy_pass http://10.10.10.1:5005;", body)
        self.assertIn("return 301 /dav/;", body)
        self.assertIn("sub_filter '<D:href>/' '<D:href>/dav/';", body)
        self.assertIn("sub_filter '<d:href>/' '<d:href>/dav/';", body)

    def test_fnos_keeps_native_configured_uri_prefix_query_and_encoding(self):
        for suffix in ("", "/", "/base/", "/base", "/base/?mode=admin", "/base%20dir/"):
            with self.subTest(suffix=suffix):
                web = "http://10.10.10.1:5666" + suffix
                dav = "http://10.10.10.1:5005" + suffix
                _, _, bodies = render_nginx(FNOS_LOCAL_URL=web, FNOS_DAV_LOCAL_URL=dav)
                body = bodies[("fnos", "web")]
                self.assertIn("proxy_pass " + web + ";", body)
                self.assertIn("proxy_pass " + dav + ";", body)
                self.assertNotIn("rewrite ^/(.*)$", body)
                self.assertIn("rewrite ^/dav/(.*)$ /$1 break;", body)
                self.assertNotIn("$request_uri", body)

    def test_xray_paths_feed_routes_application_and_bypass_from_one_definition(self):
        manager, _, bodies = render_nginx(
            NGINX_WAF_ENABLE=True, XRAY_WEBSOCKET_PATH="socket/",
            XRAY_GRPC_SERVICE_NAME="/custom.grpc/", XRAY_XHTTP_PATH="stream/",
        )
        container = manager.containers["xray-server"]
        site = manager.nginx_sites[("xray-server", "web")]
        body = bodies[("xray-server", "web")]
        self.assertIn('location = "/socket"', body)
        self.assertIn('location = "/custom.grpc"', body)
        self.assertIn('location ^~ "/stream"', body)
        self.assertEqual(str(site.vars["grpc_pattern"]), site.waf_bypass[0])
        self.assertIn('location ~ "^/custom\\\\.grpc(?:/(?:Tun|TunMulti))?$"', body)
        self.assertNotIn("${cntr_dollar}", body)
        self.assertIn('grpc_set_header "Connection" "";', body)
        self.assertIn('grpc_set_header "Upgrade" "";', body)
        for request in ("/custom.grpc", "/custom.grpc/Tun", "/custom.grpc/TunMulti"):
            self.assertIsNotNone(re.match(site.waf_bypass[0], request))
        self.assertIsNone(re.match(site.waf_bypass[0], "/customXgrpc/Tun"))
        data = json.loads(Environment().from_string((container.root_path / "config.json").read_text()).render(
            container=container, DEBUG=False, XRAY_ID="synthetic-id"))
        settings = [inbound["streamSettings"] for inbound in data["inbounds"]]
        self.assertEqual(settings[0]["wsSettings"]["path"], "/socket")
        self.assertEqual(settings[1]["grpcSettings"]["serviceName"], "/custom.grpc")
        self.assertEqual(settings[2]["xhttpSettings"]["path"], "/stream")
        self.assertEqual(body.count('grpc_set_header "X-Forwarded-Proto" "$cntr_scheme"'), 3)

    def test_business_data_is_not_rendered_a_second_time(self):
        token = "literal-{{ not_a_second_template }}"
        _, _, bodies = render_nginx(MCP_PLAYWRIGHT_TOKEN=token)
        self.assertIn("Bearer " + token, bodies[("mcp-playwright", "web")])
        for path in ROOT.glob("*/*/*.conf"):
            if path.name in ("nginx.conf", "proxy.conf"):
                self.assertIn('from "nginx/headers.j2"', path.read_text())


if __name__ == "__main__":
    unittest.main()
