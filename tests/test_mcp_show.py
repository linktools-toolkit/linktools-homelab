#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exercise MCP CLI output using only synthetic configuration."""
import argparse
from contextlib import redirect_stdout
from io import StringIO
import json
import unittest

from linktools.cli._command import SubCommandMixin
from test_navigation_integrations import make_manager


class McpShowTests(unittest.TestCase):
    def test_show_uses_resolved_site_urls_and_optional_push_channel(self):
        for https, port in ((True, 8443), (False, 8080)):
            manager = make_manager(NGINX_HTTPS_ENABLE=https,
                                   MCP_PLAYWRIGHT_TOKEN="synthetic-playwright-token",
                                   MCP_PUSH_TOKEN="synthetic-push-token")
            for name, entry, channel in (("mcp-playwright", "playwright", None),
                                         ("mcp-push", "push", None),
                                         ("mcp-push", "push", "Feishu")):
                with self.subTest(https=https, name=name, channel=channel):
                    output = StringIO()
                    with redirect_stdout(output):
                        container = manager.containers[name]
                        if channel:
                            container.on_exec_show(channel)
                        else:
                            container.on_exec_show()
                    item = json.loads(output.getvalue())["mcpServers"][entry]
                    self.assertEqual(item["url"], "%s://%s.example.test:%s/mcp" % (
                        "https" if https else "http", name, port))
                    self.assertEqual(item["headers"]["Authorization"], "Bearer synthetic-%s-token" % entry)
                    if channel:
                        self.assertEqual(item["headers"], {
                            "Authorization": "Bearer synthetic-push-token", "X-CHANNEL": "Feishu",
                            "X-FEISHU-APP-ID": "<FEISHU_APP_ID>",
                            "X-FEISHU-APP-SECRET": "<FEISHU_APP_SECRET>",
                        })
                    else:
                        self.assertEqual(set(item["headers"]), {"Authorization"})

    def test_push_channel_remains_an_optional_cli_argument(self):
        container = make_manager().containers["mcp-push"]
        commands = {command.name: command for command in SubCommandMixin().walk_subcommands(container)}
        parser = argparse.ArgumentParser()
        commands["show"].create_parser(parser.add_subparsers().add_parser)
        self.assertIsNone(parser.parse_args(["show"]).channel)
        self.assertEqual(parser.parse_args(["show", "Feishu"]).channel, "Feishu")


if __name__ == "__main__":
    unittest.main()
