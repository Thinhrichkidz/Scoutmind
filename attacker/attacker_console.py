"""
The attacker console (Flask): a small local web page with two jobs.

  1. Publish a crafted page into the page pool (data/pages/). The agent
     meets it later, while doing a normal user task. The attacker never talks
     to the agent directly, which is what makes the injection indirect.
  2. Show a live feed of the requests the attacker-simulation server has
     received (attacker/attacker_log.txt).

Run it as its own process, separate from attacker_server.py:
    python attacker/attacker_console.py        then open http://127.0.0.1:5000

Safety rules, all enforced below:
  - It listens on 127.0.0.1 only, and refuses requests from other sites.
  - Published files are always named published_<name>.html. Only files with
    that prefix can be created or removed, so the original pages in
    data/pages can never be overwritten or deleted from here.
  - It never displays a published page's HTML, and shows the log as escaped
    plain text: both are untrusted text.
Everything is fictional and local.
"""

import os
import re
from pathlib import Path

from flask import Flask, abort, render_template_string, request

HOST = "127.0.0.1"
PORT = 5000

# Resolve every path from this file, not from the folder it is launched in.
PROJECT_DIR = Path(__file__).resolve().parent.parent
PAGES_DIR = PROJECT_DIR / "data" / "pages"
ATTACKER_LOG = Path(__file__).resolve().parent / "attacker_log.txt"

PREFIX = "published_"
NAME_PATTERN = re.compile(r"^[a-z0-9_-]{1,40}$")  # what the user may type
FILE_PATTERN = re.compile(r"^published_[a-z0-9_-]{1,40}\.html$")  # what may exist
MAX_PAGE_BYTES = 100_000

FEED_LINES = 50  # how many log lines the feed shows
FEED_BYTES = 64_000  # never read more than this much of the log

# Only a browser pointed at this very address may use the console.
ALLOWED_HOSTS = {f"127.0.0.1:{PORT}", f"localhost:{PORT}"}
ALLOWED_ORIGINS = {f"http://{host}" for host in ALLOWED_HOSTS}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_PAGE_BYTES * 2  # form fields and overhead

MAIN_PAGE = """<!doctype html>
<title>ScoutMind attacker console</title>
<h1>Attacker console</h1>
<p>Local and fictional. Published pages go into data/pages, where the agent's
search can find them.</p>
{% if message %}<p><b>{{ message }}</b></p>{% endif %}

<h2>Publish a page</h2>
<form method="post" action="/publish">
  <p>Name (lowercase letters, digits, _ and -):
     <input name="name" size="30" maxlength="40" value="{{ name }}"></p>
  <p>The file will be saved as published_&lt;name&gt;.html and never replaces an existing file.</p>
  <p><textarea name="html" rows="16" cols="90">{{ html }}</textarea></p>
  <p><button type="submit">Publish</button></p>
</form>

<h2>Published pages</h2>
{% for filename in published %}
<form method="post" action="/remove">
  {{ filename }}
  <input type="hidden" name="filename" value="{{ filename }}">
  <button type="submit">Remove</button>
</form>
{% else %}
<p>None yet.</p>
{% endfor %}

<h2>Requests received by the attacker server</h2>
<iframe src="/feed" width="950" height="280"></iframe>
"""

FEED_PAGE = """<!doctype html>
<meta http-equiv="refresh" content="3">
<pre>{{ text }}</pre>
"""


@app.before_request
def only_this_browser_tab():
    """Refuse requests meant for other addresses, or sent by other websites.

    Without this, any web page you have open could quietly send a form to
    http://127.0.0.1:5000/publish and put pages into the page pool.
    """
    if request.host not in ALLOWED_HOSTS:
        abort(400)
    if request.method == "POST":
        origin = request.headers.get("Origin")
        if origin is not None and origin not in ALLOWED_ORIGINS:
            abort(403)


def check_name(name):
    """None if `name` is acceptable, otherwise a sentence saying why not."""
    if not NAME_PATTERN.fullmatch(name):
        return "The name must be 1-40 characters: lowercase letters, digits, _ or -."
    return None


def published_files():
    """The pages this console has published, in order."""
    try:
        names = sorted(os.listdir(PAGES_DIR))
    except FileNotFoundError:
        return []
    return [name for name in names if FILE_PATTERN.fullmatch(name)]


def show_main_page(message="", name="", html=""):
    return render_template_string(
        MAIN_PAGE, message=message, name=name, html=html, published=published_files()
    )


def read_feed_lines():
    """The newest lines of the attacker log (the file may not exist yet)."""
    try:
        with open(ATTACKER_LOG, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - FEED_BYTES))
            data = f.read()
    except FileNotFoundError:
        return []
    lines = data.decode("utf-8", errors="replace").splitlines()
    if size > FEED_BYTES:
        lines = lines[1:]  # the first line may have been cut in half
    return lines[-FEED_LINES:]


@app.get("/")
def index():
    return show_main_page()


@app.post("/publish")
def publish():
    name = request.form.get("name", "")
    html = request.form.get("html", "")

    problem = check_name(name)
    if problem:
        return show_main_page(problem, name, html)
    if not html.strip():
        return show_main_page("The page is empty.", name, html)
    data = html.encode("utf-8")
    if len(data) > MAX_PAGE_BYTES:
        return show_main_page(f"The page is larger than {MAX_PAGE_BYTES} bytes.", name, html)

    filename = f"{PREFIX}{name}.html"
    try:
        # "xb" creates the file and fails if it already exists, so nothing is
        # ever overwritten.
        with open(PAGES_DIR / filename, "xb") as f:
            f.write(data)
    except FileExistsError:
        return show_main_page(f"{filename} already exists. Remove it first or pick another name.", name, html)
    return show_main_page(f"Published {filename}.")


@app.post("/remove")
def remove():
    filename = request.form.get("filename", "")
    # Only the console's own files, by their exact name.
    if not FILE_PATTERN.fullmatch(filename):
        return show_main_page("That is not a page published from this console.")
    try:
        os.remove(PAGES_DIR / filename)
    except FileNotFoundError:
        return show_main_page(f"{filename} does not exist.")
    return show_main_page(f"Removed {filename}.")


@app.get("/feed")
def feed():
    lines = read_feed_lines()
    text = "\n".join(lines) if lines else "(no requests received yet)"
    return render_template_string(FEED_PAGE, text=text)


if __name__ == "__main__":
    # Never 0.0.0.0, and never debug mode (its console can run code).
    app.run(host=HOST, port=PORT, debug=False)
