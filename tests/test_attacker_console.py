"""Checks for attacker/attacker_console.py (the Flask console) and for the
experiment runner's refusal to run while published pages are present.
Flask's test client only: no real web server, and the real data/pages folder
and attacker log are never touched (temporary copies are used)."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run_experiments as exp
import tools
from attacker import attacker_console as console
from attacker import attacker_server

BASE = "http://127.0.0.1:5000"
ORIGINALS = {
    "solar_trends_2026.html": b"original solar page",
    "wind_energy_report.html": b"original wind page",
    "ev_battery_costs.html": b"original ev page",
}
BACKSLASH = chr(92)


class ConsoleTestCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.pages = self.root / "pages"
        self.pages.mkdir()
        for name, content in ORIGINALS.items():
            (self.pages / name).write_bytes(content)
        self.log = self.root / "attacker_log.txt"

        for target, value in (("PAGES_DIR", self.pages), ("ATTACKER_LOG", self.log)):
            patcher = patch.object(console, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.client = console.app.test_client()

    # helpers: every request comes from the console's own address
    def get(self, path, **kwargs):
        return self.client.get(path, base_url=BASE, **kwargs)

    def post(self, path, data, **kwargs):
        return self.client.post(path, data=data, base_url=BASE, **kwargs)

    def publish(self, name, html="<p>a page</p>"):
        return self.post("/publish", {"name": name, "html": html})

    def files(self):
        return sorted(os.listdir(self.pages))

    def assert_originals_untouched(self):
        for name, content in ORIGINALS.items():
            self.assertEqual((self.pages / name).read_bytes(), content)


class PublishTests(ConsoleTestCase):
    def test_the_first_page_shows_the_form_the_feed_and_no_pages(self):
        body = self.get("/").get_data(as_text=True)
        self.assertIn('action="/publish"', body)
        self.assertIn('<iframe src="/feed"', body)
        self.assertIn("None yet.", body)

    def test_a_page_is_saved_with_the_prefix_exactly_as_typed(self):
        html = "<html><body>café – line one\nline two</body></html>"
        response = self.publish("demo-1", html)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Published published_demo-1.html.", response.get_data(as_text=True))
        self.assertEqual((self.pages / "published_demo-1.html").read_bytes(), html.encode("utf-8"))
        self.assertIn("published_demo-1.html", self.get("/").get_data(as_text=True))
        self.assert_originals_untouched()

    def test_the_agents_search_finds_a_published_page(self):
        self.publish("battery_note", "<p>Quarterly zeppelin economics report</p>")
        with patch.object(tools, "PAGES_DIR", str(self.pages)):
            found = [page["filename"] for page in tools.search_pages("zeppelin")]
        self.assertEqual(found, ["published_battery_note.html"])

    def test_bad_names_are_refused_and_nothing_is_written(self):
        bad_names = [
            "", "Demo", "my page", "../x", "a/b", "a" + BACKSLASH + "b", "x.html", "x.y",
            "a" * 41, "café", "demo\n", " demo", "demo ", "..", ".",
        ]
        before = self.files()
        for name in bad_names:
            with self.subTest(name=name):
                body = self.publish(name).get_data(as_text=True)
                self.assertIn("The name must be 1-40 characters", body)
                self.assertEqual(self.files(), before)

    def test_name_length_boundary(self):
        self.assertIn("Published", self.publish("a" * 40).get_data(as_text=True))
        self.assertIn("must be 1-40", self.publish("b" * 41).get_data(as_text=True))

    def test_an_empty_page_is_refused(self):
        for html in ("", "   ", "\n\n"):
            with self.subTest(html=html):
                body = self.publish("empty", html).get_data(as_text=True)
                self.assertIn("The page is empty.", body)
        self.assertEqual(self.files(), sorted(ORIGINALS))

    def test_a_page_over_the_size_limit_is_refused(self):
        body = self.publish("big", "a" * (console.MAX_PAGE_BYTES + 1)).get_data(as_text=True)
        self.assertIn("larger than", body)
        self.assertEqual(self.files(), sorted(ORIGINALS))
        self.assertIn("Published", self.publish("fits", "a" * console.MAX_PAGE_BYTES).get_data(as_text=True))

    def test_a_request_far_over_the_limit_is_rejected_by_flask(self):
        response = self.publish("huge", "a" * (console.MAX_PAGE_BYTES * 3))
        self.assertEqual(response.status_code, 413)
        self.assertEqual(self.files(), sorted(ORIGINALS))

    def test_an_existing_page_is_never_overwritten(self):
        self.publish("same", "first version")
        body = self.publish("same", "second version").get_data(as_text=True)
        self.assertIn("already exists", body)
        self.assertEqual((self.pages / "published_same.html").read_bytes(), b"first version")

    def test_an_original_page_cannot_be_overwritten_by_choosing_its_name(self):
        self.publish("solar_trends_2026", "attacker content")
        self.assertIn("published_solar_trends_2026.html", self.files())
        self.assert_originals_untouched()

    def test_pages_are_never_written_outside_the_pages_folder(self):
        self.publish("x", "content")
        self.assertEqual(sorted(os.listdir(self.root)), ["pages"])  # no stray files beside it


class UntrustedContentTests(ConsoleTestCase):
    def test_a_published_pages_html_is_never_shown_by_the_console(self):
        marker = "UNIQUE_MARKER_5f3a"
        page = f"<script>alert('{marker}')</script><p>{marker}</p>"
        response = self.publish("trap", page)
        for body in (response.get_data(as_text=True), self.get("/").get_data(as_text=True)):
            self.assertNotIn(marker, body)

    def test_a_refused_form_is_given_back_escaped(self):
        body = self.publish("Bad Name", "</textarea><script>alert(1)</script>").get_data(as_text=True)
        self.assertNotIn("<script>alert(1)</script>", body)
        self.assertIn("&lt;/textarea&gt;&lt;script&gt;", body)

    def test_the_typed_name_is_shown_escaped(self):
        body = self.publish('"><script>alert(2)</script>', "x").get_data(as_text=True)
        self.assertNotIn("<script>alert(2)</script>", body)

    def test_the_log_feed_is_escaped_plain_text(self):
        self.log.write_text("[t] GET /log?data=<script>alert(3)</script>\n", encoding="utf-8")
        body = self.get("/feed").get_data(as_text=True)
        self.assertNotIn("<script>alert(3)</script>", body)
        self.assertIn("&lt;script&gt;alert(3)&lt;/script&gt;", body)


class RemoveTests(ConsoleTestCase):
    def remove(self, filename):
        return self.post("/remove", {"filename": filename}).get_data(as_text=True)

    def test_a_published_page_can_be_removed(self):
        self.publish("temp", "x")
        self.assertIn("Removed published_temp.html.", self.remove("published_temp.html"))
        self.assertEqual(self.files(), sorted(ORIGINALS))
        self.assertIn("None yet.", self.get("/").get_data(as_text=True))

    def test_the_original_pages_cannot_be_removed(self):
        for name in ORIGINALS:
            with self.subTest(name=name):
                self.assertIn("not a page published from this console", self.remove(name))
        self.assert_originals_untouched()

    def test_only_exact_published_names_are_accepted(self):
        outside = self.root / "outside.html"
        outside.write_text("keep me")
        self.publish("keep", "x")
        bad = [
            "../outside.html", "published_/../../outside.html", "published_x.html\n",
            "published_x.html.bak", "published_.html", "Published_x.html", "published_X.html",
            "published_x.htm", "published_" + BACKSLASH + "..", "../pages/published_keep.html",
            "", "published_" + "a" * 41 + ".html",
        ]
        for name in bad:
            with self.subTest(name=name):
                self.assertIn("not a page published from this console", self.remove(name))
        self.assertEqual(outside.read_text(), "keep me")
        self.assertIn("published_keep.html", self.files())

    def test_removing_a_missing_page_says_so(self):
        self.assertIn("does not exist", self.remove("published_ghost.html"))


class FeedTests(ConsoleTestCase):
    def test_no_log_yet(self):
        self.assertFalse(self.log.exists())
        self.assertIn("(no requests received yet)", self.get("/feed").get_data(as_text=True))

    def test_an_empty_log(self):
        self.log.write_bytes(b"")
        self.assertIn("(no requests received yet)", self.get("/feed").get_data(as_text=True))

    def test_the_feed_shows_the_requests_and_refreshes_itself(self):
        self.log.write_text("[t1] GET /log?data=one\n[t2] GET /log?data=two\n", encoding="utf-8")
        body = self.get("/feed").get_data(as_text=True)
        self.assertIn("GET /log?data=one", body)
        self.assertIn("GET /log?data=two", body)
        self.assertIn('http-equiv="refresh"', body)

    def test_only_the_newest_lines_are_shown(self):
        lines = [f"[t] GET /log?data=line{i:04d}" for i in range(console.FEED_LINES + 30)]
        self.log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        shown = console.read_feed_lines()
        self.assertEqual(len(shown), console.FEED_LINES)
        self.assertEqual(shown[-1], lines[-1])
        self.assertEqual(shown[0], lines[-console.FEED_LINES])

    def test_a_huge_log_is_read_only_from_the_end_and_never_starts_mid_line(self):
        line = "[t] GET /log?data=" + "y" * 80
        count = (console.FEED_BYTES * 3) // len(line)
        self.log.write_text("\n".join(f"{line}{i:06d}" for i in range(count)) + "\n", encoding="utf-8")
        shown = console.read_feed_lines()
        self.assertLessEqual(len(shown), console.FEED_LINES)
        for entry in shown:
            self.assertTrue(entry.startswith("[t] GET /log?data="), entry[:30])
        self.assertTrue(shown[-1].endswith(f"{count - 1:06d}"))

    def test_long_lines_never_leave_a_half_line_at_the_top_of_the_feed(self):
        # With long lines the 64 KB window holds fewer than FEED_LINES lines,
        # so a half-cut first line would be shown if it were not dropped.
        line = "[t] GET /log?data=" + "z" * 3000
        count = (console.FEED_BYTES * 2) // len(line)
        self.log.write_text("\n".join(f"{line}{i:04d}" for i in range(count)) + "\n", encoding="utf-8")
        shown = console.read_feed_lines()
        self.assertLess(len(shown), console.FEED_LINES)
        self.assertGreater(len(shown), 5)
        for entry in shown:
            self.assertEqual(len(entry), len(line) + 4)  # every line complete

    def test_at_most_the_last_feed_bytes_are_read_from_the_file(self):
        self.log.write_text("[t] GET /log?data=" + "q" * 100 + "\n" * 1, encoding="utf-8")
        with open(self.log, "ab") as f:
            f.write((b"[t] GET /log?data=" + b"r" * 100 + b"\n") * (console.FEED_BYTES // 100))
        real_open = open
        amounts = []

        class Spy:
            def __init__(self, path, mode):
                self.file = real_open(path, mode)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.file.close()

            def seek(self, *args):
                return self.file.seek(*args)

            def tell(self):
                return self.file.tell()

            def read(self, *args):
                data = self.file.read(*args)
                amounts.append(len(data))
                return data

        with patch.object(console, "open", Spy, create=True):
            console.read_feed_lines()
        self.assertEqual(len(amounts), 1)
        self.assertLessEqual(amounts[0], console.FEED_BYTES)

    def test_bytes_that_are_not_text_do_not_crash_the_feed(self):
        self.log.write_bytes(b"[t] GET /log?data=\xff\xfe\x80 ok\n")
        response = self.get("/feed")
        self.assertEqual(response.status_code, 200)
        self.assertIn("ok", response.get_data(as_text=True))

class OnlyThisBrowserTests(ConsoleTestCase):
    def test_another_host_name_is_refused(self):
        for host in ("evil.example", "127.0.0.1:6000", "127.0.0.1", "0.0.0.0:5000"):
            with self.subTest(host=host):
                self.assertEqual(self.client.get("/", base_url=f"http://{host}").status_code, 400)

    def test_localhost_with_the_right_port_is_accepted(self):
        self.assertEqual(self.client.get("/", base_url="http://localhost:5000").status_code, 200)

    def test_a_form_from_another_site_cannot_publish_or_remove(self):
        self.publish("mine", "x")
        for origin in ("http://evil.example", "http://127.0.0.1:6000", "null", "https://127.0.0.1:5000"):
            with self.subTest(origin=origin):
                headers = {"Origin": origin}
                published = self.post("/publish", {"name": "stolen", "html": "x"}, headers=headers)
                removed = self.post("/remove", {"filename": "published_mine.html"}, headers=headers)
                self.assertEqual(published.status_code, 403)
                self.assertEqual(removed.status_code, 403)
        self.assertEqual(self.files(), sorted(list(ORIGINALS) + ["published_mine.html"]))

    def test_the_consoles_own_origin_is_accepted(self):
        origins = {"http://127.0.0.1:5000": "from-ip", "http://localhost:5000": "from-name"}
        for origin, name in origins.items():
            with self.subTest(origin=origin):
                response = self.post("/publish", {"name": name, "html": "x"},
                                     headers={"Origin": origin})
                self.assertEqual(response.status_code, 200)
                self.assertIn(f"published_{name}.html", self.files())

    def test_a_post_without_an_origin_header_is_accepted(self):
        # Non-browser clients (and the tests) send none; browsers always do.
        self.assertEqual(self.publish("noorigin", "x").status_code, 200)


class SettingsTests(unittest.TestCase):
    def test_it_listens_on_loopback_only_and_never_in_debug_mode(self):
        self.assertEqual(console.HOST, "127.0.0.1")
        source = Path(console.__file__).read_text(encoding="utf-8")
        self.assertIn("app.run(host=HOST, port=PORT, debug=False)", source)

    def test_the_default_folders_are_the_projects_own(self):
        project = Path(exp.PROJECT_DIR)
        self.assertEqual(console.PAGES_DIR.resolve(), (project / "data" / "pages").resolve())
        self.assertEqual(console.ATTACKER_LOG.resolve(),
                         (project / "attacker" / "attacker_log.txt").resolve())

    def test_the_feed_reads_the_file_the_attacker_server_writes(self):
        self.assertEqual(Path(attacker_server.LOG_FILE).resolve(), console.ATTACKER_LOG.resolve())

    def test_the_prefix_matches_the_experiment_runners_guard(self):
        self.assertEqual(console.PREFIX, exp.PUBLISHED_PREFIX)

    def test_the_port_is_not_one_of_the_projects_other_servers(self):
        used = {exp.ATTACKER_SERVER["port"], exp.CDN_SERVER["port"], 8501, 11434}
        self.assertNotIn(console.PORT, used)


class ExperimentGuardTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.pages = directory.name
        for name in ORIGINALS:
            Path(self.pages, name).write_bytes(b"x")
        for patcher in (patch.object(tools, "PAGES_DIR", self.pages),
                        patch("run_experiments.non_empty_files", return_value=[])):
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_main(self, argv):
        with patch("run_experiments.run_condition") as run_condition:
            try:
                exp.main(argv)
                code = None
            except SystemExit as e:
                code = e.code
        return run_condition, code

    def test_no_published_pages_means_no_problem(self):
        self.assertEqual(exp.leftover_published_pages(), [])
        run_condition, code = self.run_main(["--trials", "1"])
        self.assertIsNone(code)
        self.assertEqual(run_condition.call_count, 2)

    def test_a_leftover_published_page_stops_the_experiment_before_anything_runs(self):
        Path(self.pages, "published_demo.html").write_bytes(b"x")
        Path(self.pages, "published_other.html").write_bytes(b"x")
        self.assertEqual(exp.leftover_published_pages(),
                         ["published_demo.html", "published_other.html"])
        run_condition, code = self.run_main(["--trials", "1"])
        self.assertEqual(code, 2)
        run_condition.assert_not_called()

    def test_the_guard_applies_to_every_scenario_and_setting(self):
        Path(self.pages, "published_demo.html").write_bytes(b"x")
        for argv in (["--scenario", "cdn"], ["--scenario", "all"], ["--only", "on"]):
            with self.subTest(argv=argv):
                run_condition, code = self.run_main(argv + ["--trials", "1"])
                self.assertEqual(code, 2)
                run_condition.assert_not_called()

    def test_a_missing_pages_folder_is_not_a_crash(self):
        with patch.object(tools, "PAGES_DIR", os.path.join(self.pages, "no_such_folder")):
            self.assertEqual(exp.leftover_published_pages(), [])


if __name__ == "__main__":
    unittest.main()
