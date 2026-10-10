#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Homelab callback declarations consumed by the real shared Authelia client."""
from pathlib import Path
from types import MappingProxyType
import unittest

import linktools.cntr
from linktools.cntr.ext import Authelia
from test_navigation_integrations import load_container, make_manager


def shared_client(manager):
    source = Path(linktools.cntr.__file__).parent.parent / "assets/containers/102-authelia/container.py"
    authelia = load_container(source)(manager, source.parent, "authelia")
    # Only the already-existing client identity is synthetic; callback collection
    # uses the real installed declarations, factories, URLs and consumer method.
    authelia.__dict__["_oidc_identity"] = MappingProxyType({
        "issuer_url": "https://auth.example.test", "client_id": "existing-client",
        "client_name": "Existing shared client", "client_secret": "synthetic-existing-secret",
    })
    return authelia.oidc_client


class OidcIntegrationTests(unittest.TestCase):
    def test_three_producers_contribute_to_one_existing_shared_client(self):
        manager = make_manager(NGINX_AUTH_ENABLE=True, PVE_LOCAL_URL="https://192.0.2.10:8006/")
        declarations = list(manager.iter_integrations("authelia"))
        self.assertEqual([producer.name for producer, _, _ in declarations], ["litellm", "gitlab", "homelab"])
        self.assertTrue(all(isinstance(value, Authelia) for _, _, value in declarations))
        self.assertEqual(manager.env_config.reads, [])
        client = shared_client(manager)
        self.assertEqual(client["client_id"], "existing-client")
        self.assertEqual(client["client_secret"], "synthetic-existing-secret")
        self.assertEqual(client["redirect_uris"], (
            "https://auth.example.test",
            "https://litellm.example.test:8443/sso/callback",
            "https://gitlab.example.test:8443/users/auth/openid_connect/callback",
            "https://pve.example.test:8443",
            "https://192.0.2.10:8006/",
        ))
        with self.assertRaises(TypeError):
            client["client_id"] = "another-client"

    def test_disabled_auth_does_not_resolve_callback_configuration(self):
        manager = make_manager(NGINX_AUTH_ENABLE=False)
        self.assertEqual(shared_client(manager)["redirect_uris"], ("https://auth.example.test",))
        self.assertEqual(set(manager.env_config.reads), {"NGINX_AUTH_ENABLE"})

    def test_disabled_sites_do_not_leave_stale_callbacks(self):
        manager = make_manager(NGINX_AUTH_ENABLE=True, GITLAB_DOMAIN="", LITELLM_DOMAIN="",
                               PVE_DOMAIN="", PVE_LOCAL_URL="https://192.0.2.10:8006/")
        self.assertEqual(shared_client(manager)["redirect_uris"], ("https://auth.example.test",))
        manager = make_manager(NGINX_AUTH_ENABLE=True, PVE_LOCAL_URL="")
        self.assertFalse(any("pve" in value or "192.0.2.10" in value
                             for value in shared_client(manager)["redirect_uris"]))

    def test_proxmox_local_trailing_slash_query_and_duplicate_behavior(self):
        for local in ("https://192.0.2.10:8006", "https://192.0.2.10:8006/",
                      "https://192.0.2.10:8006/?mode=login", "https://pve.example.test:8443"):
            with self.subTest(local=local):
                manager = make_manager(NGINX_AUTH_ENABLE=True, PVE_LOCAL_URL=local)
                redirects = shared_client(manager)["redirect_uris"]
                self.assertIn(local, redirects)
                self.assertEqual(redirects.count(local), 1)
                self.assertEqual(redirects.count("https://pve.example.test:8443"), 1)


if __name__ == "__main__":
    unittest.main()
