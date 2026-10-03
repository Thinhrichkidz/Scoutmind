"""Small standard-library checks; no agent, model, or external network calls."""

import contextlib
import io
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch

import config
import tools
from servers.image_source_server import ImageSourceHandler


class LocalTestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.server.received_paths.append(self.path)
        # /redirect-302 and /redirect-307 answer with that redirect status code.
        if self.path in ("/redirect-302", "/redirect-307"):
            self.send_response(int(self.path[-3:]))
            self.send_header(
                "Location",
                f"http://127.0.0.1:{self.server.server_port}/redirect-target",
            )
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass


class ContainmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Port 0 chooses a free local port, avoiding the demo servers' ports.
        cls.server = HTTPServer(("127.0.0.1", 0), LocalTestHandler)
        cls.server.received_paths = []
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()

    def setUp(self):
        # Suppress routine tool prints; unittest reports each check by name.
        output = contextlib.redirect_stdout(io.StringIO())
        output.__enter__()
        self.addCleanup(output.__exit__, None, None, None)
        self.server.received_paths.clear()

        # Test-only: also permit this test server's random port, so the tests
        # never need the real demo servers on 8001 or 9000 to be running.
        ports = tools.CONTAINMENT_PORTS | {self.server.server_port}
        port_patch = patch.object(tools, "CONTAINMENT_PORTS", ports)
        port_patch.start()
        self.addCleanup(port_patch.stop)

        # Test-only: permit this test server's origin while each test runs.
        origins = config.ALLOWED_ORIGINS + [self.base_url]
        origin_patch = patch.object(config, "ALLOWED_ORIGINS", origins)
        origin_patch.start()
        self.addCleanup(origin_patch.stop)

    def test_accepts_exact_loopback_http_and_https_urls(self):
        urls = [
            "http://127.0.0.1:8001/image?data=fake%20value",
            "https://127.0.0.1:8001/image",
            "http://127.0.0.1:9000/log",
            "HTTP://127.0.0.1:9000/log",
        ]
        for url in urls:
            with self.subTest(url=url):
                tools.validate_image_url(url)

    def test_rejects_hosts_schemes_ports_and_userinfo(self):
        urls = [
            "http://localhost:8001/",
            "http://[::1]:8001/",
            "http://example.test/",
            "http://127.0.0.2:8001/",
            # Other spellings of 127.0.0.1 that some resolvers accept.
            "http://2130706433:8001/",
            "http://0x7f.0.0.1:8001/",
            "http://0177.0.0.1:8001/",
            "http://127.1:8001/",
            "http://127.000.000.001:8001/",
            "http://127.0.0.1.:8001/",
            "http://127.0.0.1%2e:8001/",
            "http://127.0.0.1\\@example.test:8001/",
            "ftp://127.0.0.1:8001/image",
            "file://127.0.0.1:8001/image",
            # Ports: missing, not a demo port, zero-padded, invalid.
            "http://127.0.0.1/",
            "https://127.0.0.1/",
            "http://127.0.0.1:11434/api/tags",
            "http://127.0.0.1:65535/",
            "http://127.0.0.1:08001/",
            "http://127.0.0.1:abc/",
            "http://127.0.0.1:-1/",
            "http://127.0.0.1:0/",
            "http://127.0.0.1:65536/",
            "http://127.0.0.1:/",
            "http://127.0.0.1@example.test/",
            "http://example.test@127.0.0.1:8001/",
            "http://user:password@127.0.0.1:8001/",
            "http://127.0.0.1:8001/fake value",
            "http://127.0.0.1\n:8001/",
            "http://[127.0.0.1/",
            "",
        ]
        for enabled in (False, True):
            with patch.object(config, "DEFENCE_ENABLED", enabled):
                for url in urls:
                    with self.subTest(defence_enabled=enabled, url=url):
                        with patch("tools.defence.check_url") as defence_check:
                            with patch("tools.urllib.request.build_opener") as build_opener:
                                result = tools.render_image(url)
                        self.assertIn("refused by containment", result)
                        defence_check.assert_not_called()
                        build_opener.assert_not_called()

    def test_local_get_succeeds_with_defence_off_and_on(self):
        for enabled in (False, True):
            with self.subTest(defence_enabled=enabled):
                with patch.object(config, "DEFENCE_ENABLED", enabled):
                    result = tools.render_image(self.base_url + "/ok")
                self.assertEqual(result, "Image request succeeded (status 200).")
        self.assertEqual(self.server.received_paths, ["/ok", "/ok"])

    def test_toggleable_defence_can_block_after_containment(self):
        with patch("tools.defence.check_url", side_effect=ValueError("test rejection")):
            result = tools.render_image(self.base_url + "/ok")
        self.assertEqual(result, "Image request rejected: test rejection")
        self.assertEqual(self.server.received_paths, [])

    def test_redirect_is_refused_without_requesting_its_local_target(self):
        for path in ("/redirect-302", "/redirect-307"):
            for enabled in (False, True):
                with self.subTest(path=path, defence_enabled=enabled):
                    self.server.received_paths.clear()
                    with patch.object(config, "DEFENCE_ENABLED", enabled):
                        result = tools.render_image(self.base_url + path)
                    self.assertIn("Redirects are refused", result)
                    self.assertEqual(self.server.received_paths, [path])

    def test_proxy_settings_are_ignored(self):
        # The proxy is also loopback. A proxied request would have an absolute
        # URL in its request path, whereas a direct request has only /ok.
        proxy_settings = {
            "http_proxy": self.base_url,
            "HTTP_PROXY": self.base_url,
            "https_proxy": self.base_url,
            "HTTPS_PROXY": self.base_url,
            "all_proxy": self.base_url,
            "ALL_PROXY": self.base_url,
            "no_proxy": "",
            "NO_PROXY": "",
        }
        with patch.dict(os.environ, proxy_settings):
            result = tools.render_image(self.base_url + "/ok")
        self.assertEqual(result, "Image request succeeded (status 200).")
        self.assertEqual(self.server.received_paths, ["/ok"])

    def test_page_access_works_from_another_project_directory(self):
        original_directory = os.getcwd()
        try:
            os.chdir(os.path.join(tools.PROJECT_DIR, "tests"))
            matches = tools.search_pages("energy")
            self.assertEqual(
                [page["filename"] for page in matches],
                ["ev_battery_costs.html", "solar_trends_2026.html", "wind_energy_report.html"],
            )
            self.assertIn("Global Solar Energy", tools.read_page("solar_trends_2026.html"))
            self.assertIn("Refused:", tools.read_page("../../CLAUDE.md"))
        finally:
            os.chdir(original_directory)

    def test_read_page_refuses_absolute_paths(self):
        # os.path.join discards PAGES_DIR when the second part is absolute.
        absolute = os.path.join(tools.PROJECT_DIR, "config.py")
        self.assertIn("Refused:", tools.read_page(absolute))

    @unittest.skipUnless(os.name == "nt", "backslash is a separator only on Windows")
    def test_read_page_refuses_windows_style_traversal(self):
        self.assertIn("Refused:", tools.read_page("..\\..\\config.py"))

    def test_read_page_refuses_a_sibling_folder_with_a_similar_name(self):
        # A folder such as data/pages_abc123 starts with the same text as
        # data/pages. A plain startswith() check would wrongly allow it.
        data_dir = os.path.join(tools.PROJECT_DIR, "data")
        with tempfile.TemporaryDirectory(prefix="pages_", dir=data_dir) as sibling:
            secret = os.path.join(sibling, "secret.html")
            with open(secret, "w", encoding="utf-8") as f:
                f.write("fake secret")
            relative = "../" + os.path.basename(sibling) + "/secret.html"
            self.assertIn("Refused:", tools.read_page(relative))

    def test_search_skips_a_candidate_resolving_outside_the_page_pool(self):
        # Simulate a link without requiring Windows symlink privileges.
        escaped_path = os.path.join(tools.PROJECT_DIR, "attacker", "escaped.html")
        with patch("tools.os.listdir", return_value=["escaped.html"]):
            with patch("tools.os.path.realpath", side_effect=[tools.PAGES_DIR, escaped_path]):
                with patch("builtins.open") as open_file:
                    self.assertEqual(tools.search_pages("energy"), [])
        open_file.assert_not_called()

    def test_legitimate_image_handler_returns_a_fixed_response(self):
        server = HTTPServer(("127.0.0.1", 0), ImageSourceHandler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            # Exercise the actual handler without occupying its demo port 8001.
            opener = tools.urllib.request.build_opener(tools.urllib.request.ProxyHandler({}))
            with opener.open(f"http://127.0.0.1:{server.server_port}/image", timeout=5) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.read(), b"OK")
        finally:
            server.shutdown()
            thread.join()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
