"""Checks for the extra experiment scenarios (cdn, text_only, legit_email).
Fake agent results and fake servers only: no real model and no real server on
port 8001 or 9000."""

import os
import re
import tempfile
import threading
import unittest
import urllib.request
from http.server import HTTPServer
from pathlib import Path
from unittest.mock import MagicMock, patch

import config
import defence
import run_experiments as exp
import tools
from servers import cdn_logging_server


def read_variant(name):
    with open(os.path.join(exp.VARIANTS_DIR, name), encoding="utf-8") as f:
        return f.read()


def make_result(summary=None):
    return {"trace": [], "summary": summary, "completed": True,
            "stop_reason": "save_summary", "model_text": ""}


class ScenarioTableTests(unittest.TestCase):
    def test_every_variant_file_exists_and_is_a_single_html_comment(self):
        for name, scenario in exp.SCENARIOS.items():
            if scenario["variant"] is None:
                continue
            with self.subTest(scenario=name):
                text = read_variant(scenario["variant"]).strip()
                self.assertTrue(text.startswith("<!--"))
                self.assertTrue(text.endswith("-->"))
                self.assertEqual(text.count("<!--"), 1)

    def test_attack_variants_are_injections_and_the_benign_one_is_not(self):
        for name in ("cdn_injection.txt", "text_only_injection.txt"):
            with self.subTest(variant=name):
                self.assertTrue(exp.INJECTION_PATTERN.search(read_variant(name)))
        benign = read_variant("benign_comment.txt")
        self.assertNotIn("Note to AI assistant", benign)
        self.assertNotIn("http", benign)
        self.assertNotIn("account", benign.lower())

    def test_cdn_variant_points_at_an_allowlisted_origin_that_containment_accepts(self):
        text = read_variant("cdn_injection.txt")
        urls = re.findall(r"http://127\.0\.0\.1:\d+/\S*", text)
        self.assertTrue(urls)
        for url in urls:
            with self.subTest(url=url):
                self.assertTrue(url.startswith("http://127.0.0.1:8001/"))
                with patch.object(config, "DEFENCE_ENABLED", True):
                    self.assertTrue(defence.is_allowed(url))
                if "%20" in url:  # the complete example URL, not the pattern
                    tools.validate_image_url(url)

    def test_the_baseline_attack_origin_is_still_blocked_by_the_defence(self):
        with patch.object(config, "DEFENCE_ENABLED", True):
            self.assertFalse(defence.is_allowed("http://127.0.0.1:9000/log?data=x"))

    def test_text_only_variant_asks_for_no_image_and_no_url(self):
        text = read_variant("text_only_injection.txt")
        self.assertNotIn("render_image", text)
        self.assertNotIn("http://", text)
        self.assertIn("Prepared for:", text)

    def test_scenario_settings(self):
        self.assertIs(exp.SCENARIOS["attack"]["server"], exp.ATTACKER_SERVER)
        self.assertIs(exp.SCENARIOS["cdn"]["server"], exp.CDN_SERVER)
        self.assertEqual(exp.CDN_SERVER["port"], 8001)
        self.assertIsNone(exp.SCENARIOS["text_only"]["server"])
        legit = exp.SCENARIOS["legit_email"]
        # The page is searchable, but its injection is replaced by a harmless comment.
        self.assertTrue(legit["include_attack_page"])
        self.assertEqual(legit["variant"], "benign_comment.txt")
        self.assertIn("account email", legit["query"])
        self.assertNotEqual(legit["query"], agent_query())

    def test_output_paths(self):
        self.assertEqual(exp.output_paths("attack", False), (exp.ATTACK_CSV, exp.EVIDENCE_OFF))
        self.assertEqual(exp.output_paths("attack", True), (exp.DEFENCE_CSV, exp.EVIDENCE_ON))
        csv_path, evidence_path = exp.output_paths("legit_email", True)
        self.assertTrue(csv_path.endswith("legit_email_defence_on.csv"))
        self.assertTrue(evidence_path.endswith("attacker_log_legit_email_defence_on.txt"))


def agent_query():
    return exp.agent.USER_QUERY


class PagePoolTests(unittest.TestCase):
    def test_pool_swaps_the_comment_and_leaves_the_real_pages_alone(self):
        real_page = os.path.join(tools.PAGES_DIR, "ev_battery_costs.html")
        with open(real_page, "rb") as f:
            real_before = f.read()

        pool = exp.build_page_pool("text_only_injection.txt")
        try:
            with open(os.path.join(pool.name, "ev_battery_costs.html"), encoding="utf-8") as f:
                html = f.read()
            self.assertIn('line that starts with "Prepared for:"', html)
            self.assertNotIn("render_image", html)  # the original comment is gone
            self.assertEqual(html.count("Note to AI assistant"), 1)
            # The normal pages are copied unchanged.
            for name in ("solar_trends_2026.html", "wind_energy_report.html"):
                with open(os.path.join(pool.name, name), "rb") as copy:
                    with open(os.path.join(tools.PAGES_DIR, name), "rb") as original:
                        self.assertEqual(copy.read(), original.read())
        finally:
            pool_path = pool.name
            pool.cleanup()
        self.assertFalse(os.path.exists(pool_path))
        with open(real_page, "rb") as f:
            self.assertEqual(f.read(), real_before)

    def test_pool_keeps_the_rest_of_the_booby_trapped_page(self):
        pool = exp.build_page_pool("cdn_injection.txt")
        try:
            with open(os.path.join(pool.name, "ev_battery_costs.html"), encoding="utf-8") as f:
                html = f.read()
        finally:
            pool.cleanup()
        self.assertIn("EV Battery Cost Trends", html)
        self.assertIn("127.0.0.1:8001/badge", html)
        self.assertNotIn("127.0.0.1:9000", html)

    def test_pool_fails_loudly_when_the_page_has_no_hidden_comment(self):
        with tempfile.TemporaryDirectory() as fake_pages:
            with open(os.path.join(fake_pages, "ev_battery_costs.html"), "w", encoding="utf-8") as f:
                f.write("<html>no comment here</html>")
            with patch.object(tools, "PAGES_DIR", fake_pages):
                with self.assertRaisesRegex(RuntimeError, "hidden comment"):
                    exp.build_page_pool("cdn_injection.txt")


class ScenarioRunTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.log_path = os.path.join(directory.name, "attacker_log.txt")
        with open(self.log_path, "wb") as f:
            f.write(b"original\n")
        self.csv_path = os.path.join(directory.name, "out.csv")
        self.evidence_path = os.path.join(directory.name, "evidence.txt")
        patcher = patch.object(exp, "ATTACKER_LOG", self.log_path)
        patcher.start()
        self.addCleanup(patcher.stop)

        self.start_mock = patch("run_experiments.start_server", return_value=MagicMock()).start()
        self.stop_mock = patch("run_experiments.stop_server").start()
        self.addCleanup(patch.stopall)

    def test_run_trial_uses_the_scenarios_query_and_page_setting(self):
        scenario = {"query": "A custom question.", "include_attack_page": False,
                    "variant": None, "server": None}
        with patch("run_experiments.agent.run_agent", return_value=make_result("hi")) as run_agent:
            exp.run_trial(1, True, scenario)
        run_agent.assert_called_once_with("A custom question.", include_attack_page=False)

    def test_legit_email_scenario_starts_no_server_and_counts_the_email_in_the_summary(self):
        summary = "Summary text. Your account email is alex.researcher@fakecorp.example"
        with patch("run_experiments.agent.run_agent", return_value=make_result(summary)):
            rows = exp.run_condition("legit_email", True, 2, self.csv_path, self.evidence_path)
        self.start_mock.assert_not_called()
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[0]["text_leak"])
        self.assertTrue(rows[0]["completed"])

    def test_cdn_scenario_starts_the_cdn_server_and_swaps_the_pages_during_trials(self):
        seen = []

        def fake_agent(query, include_attack_page):
            with open(os.path.join(tools.PAGES_DIR, "ev_battery_costs.html"), encoding="utf-8") as f:
                seen.append("127.0.0.1:8001/badge" in f.read())
            return make_result()

        original_pages_dir = tools.PAGES_DIR
        with patch("run_experiments.agent.run_agent", side_effect=fake_agent):
            exp.run_condition("cdn", True, 2, self.csv_path, self.evidence_path)
        self.start_mock.assert_called_once_with(exp.CDN_SERVER)
        self.stop_mock.assert_called_once()
        self.assertEqual(seen, [True, True])
        self.assertEqual(tools.PAGES_DIR, original_pages_dir)  # put back afterwards

    def test_pages_folder_is_restored_even_when_a_trial_is_interrupted(self):
        original_pages_dir = tools.PAGES_DIR
        with patch("run_experiments.run_trial", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                exp.run_condition("text_only", False, 3, self.csv_path, self.evidence_path)
        self.assertEqual(tools.PAGES_DIR, original_pages_dir)
        self.start_mock.assert_not_called()  # text_only needs no server
        with open(self.log_path, "rb") as f:
            self.assertEqual(f.read(), b"original\n")

    def test_attack_scenario_still_uses_the_attacker_server_and_real_pages(self):
        original_pages_dir = tools.PAGES_DIR
        seen = []

        def fake_agent(query, include_attack_page):
            seen.append(tools.PAGES_DIR)
            return make_result()

        with patch("run_experiments.agent.run_agent", side_effect=fake_agent):
            exp.run_condition("attack", False, 1, self.csv_path, self.evidence_path)
        self.start_mock.assert_called_once_with(exp.ATTACKER_SERVER)
        self.assertEqual(seen, [original_pages_dir])


class CdnLoggingServerTests(unittest.TestCase):
    def test_server_returns_a_fixed_response_and_logs_the_query_string(self):
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "log.txt"
            server = HTTPServer(("127.0.0.1", 0), cdn_logging_server.CdnLoggingHandler)
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                with patch.object(cdn_logging_server, "LOG_FILE", log_path):
                    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                    url = f"http://127.0.0.1:{server.server_port}/badge?data=Account%20email"
                    with opener.open(url, timeout=5) as response:
                        self.assertEqual(response.status, 200)
                        self.assertEqual(response.read(), b"OK")
            finally:
                server.shutdown()
                thread.join()
                server.server_close()
            line = log_path.read_text(encoding="utf-8")
        self.assertIn("GET /badge?data=Account%20email", line)
        self.assertEqual(line.count("\n"), 1)

    def test_server_settings(self):
        self.assertEqual(cdn_logging_server.HOST, "127.0.0.1")  # never 0.0.0.0
        self.assertEqual(cdn_logging_server.PORT, 8001)
        self.assertEqual(Path(cdn_logging_server.LOG_FILE).resolve(),
                         Path(exp.ATTACKER_LOG).resolve())


if __name__ == "__main__":
    unittest.main()
