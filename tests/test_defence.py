"""Origin allowlist checks using unittest; no servers or model are started."""

import unittest
from unittest.mock import patch

import config
import defence
import tools


class DefenceTests(unittest.TestCase):
    def test_defence_on_allows_legitimate_origin(self):
        url = "http://127.0.0.1:8001/image?label=fake"
        with patch.object(config, "DEFENCE_ENABLED", True):
            self.assertTrue(defence.is_allowed(url))
            defence.check_url(url)

    def test_defence_on_blocks_attacker_port(self):
        url = "http://127.0.0.1:9000/log?data=fake"
        with patch.object(config, "DEFENCE_ENABLED", True):
            self.assertFalse(defence.is_allowed(url))
            with self.assertRaisesRegex(ValueError, "origin 'http://127.0.0.1:9000'"):
                defence.check_url(url)

    def test_defence_on_blocks_different_scheme(self):
        with patch.object(config, "DEFENCE_ENABLED", True):
            with self.assertRaisesRegex(ValueError, "origin 'https://127.0.0.1:8001'"):
                defence.check_url("https://127.0.0.1:8001/")

    def test_defence_on_blocks_missing_port(self):
        url = "http://127.0.0.1/image"
        self.assertIsNone(defence.get_origin(url))
        with patch.object(config, "DEFENCE_ENABLED", True):
            with self.assertRaises(ValueError) as error:
                defence.check_url(url)
        self.assertEqual(
            str(error.exception),
            "Blocked by defence: origin could not be determined (explicit port required)",
        )

    def test_defence_off_does_not_parse_or_reject_any_url(self):
        urls = [
            "http://127.0.0.1:8001/",
            "http://127.0.0.1:9000/log?data=fake",
            "https://127.0.0.1:8001/",
            "http://127.0.0.1/",
            "http://127.0.0.1:invalid/",
            None,
        ]
        with patch.object(config, "DEFENCE_ENABLED", False):
            with patch("defence.get_origin") as get_origin:
                for url in urls:
                    with self.subTest(url=url):
                        defence.check_url(url)
                get_origin.assert_not_called()

    def test_render_image_rejects_attacker_without_network_request(self):
        with patch.object(config, "DEFENCE_ENABLED", True):
            # The real containment guard and defence both run. The network
            # opener must never be built for the blocked attacker origin.
            with patch("tools.urllib.request.build_opener") as build_opener:
                result = tools.render_image("http://127.0.0.1:9000/log?data=fake")
        self.assertTrue(result.startswith("Image request rejected"))
        self.assertIn("http://127.0.0.1:9000", result)
        build_opener.assert_not_called()

    def test_get_origin_ignores_path_query_and_fragment(self):
        self.assertEqual(
            defence.get_origin("http://127.0.0.1:8001/image?label=fake#preview"),
            "http://127.0.0.1:8001",
        )

    def test_invalid_ports_do_not_match_allowlist(self):
        for url in ("http://127.0.0.1:invalid/", "http://127.0.0.1:65536/"):
            with self.subTest(url=url):
                self.assertIsNone(defence.get_origin(url))
                self.assertFalse(defence.is_allowed(url))


if __name__ == "__main__":
    unittest.main()
