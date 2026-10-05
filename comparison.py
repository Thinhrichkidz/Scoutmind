"""
Plain helper functions for the comparison view in app.py.

They turn the result of agent.run_agent into things the page can show:
table rows for the tool-call trace, and short plain-English findings that
point out what the user would never see in the answer. No Streamlit code
here, so the functions are easy to test.
"""

import json
import textwrap
from urllib.parse import unquote

from run_experiments import FAKE_EMAIL, FAKE_KEY, classify_image_result, shown_text

# What each render_image outcome means, in words for the page.
OUTCOME_TEXT = {
    "succeeded": "the request went through",
    "rejected_by_defence": "blocked by the defence",
    "refused_by_containment": "refused by the sandbox containment",
    "failed": "the request failed",
}

# These two tools are the ones the attack needs; the other three are the
# normal research tools.
PRIVILEGED_TOOLS = {"lookup_account_info", "render_image"}

RESULT_PREVIEW_LENGTH = 150

# st.text never wraps, so long lines would run off the edge of the page.
# wrap_text() breaks them first. (A module setting so tests can change it.)
WRAP_WIDTH = 70


def shorten(text, limit=RESULT_PREVIEW_LENGTH):
    """One line, cut to `limit` characters (page results are very long)."""
    text = str(text).replace("\n", " ")
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def wrap_text(text, width=None):
    """Break long lines so plain text fits the page. Blank lines are kept, and
    a very long word (such as a URL) is broken rather than left to overflow."""
    if width is None:
        width = WRAP_WIDTH
    lines = []
    for line in str(text).splitlines() or [""]:
        lines.extend(textwrap.wrap(line, width) or [""])
    return "\n".join(lines)


def image_url(entry):
    """The URL a render_image call was given, decoded so leaked data is
    readable. The model controls the arguments, so tolerate anything."""
    arguments = entry["arguments"]
    url = ""
    if isinstance(arguments, dict):
        url = arguments.get("url")
    if not isinstance(url, str) or not url:
        return "(no valid URL given)"
    return unquote(url)


def trace_rows(trace):
    """One table row per tool call, in the order the calls happened."""
    rows = []
    for entry in trace:
        privileged = ""
        if entry["tool"] in PRIVILEGED_TOOLS:
            privileged = "yes"
        rows.append({
            "step": entry["step"],
            "tool": entry["tool"],
            "privileged": privileged,
            "arguments": shorten(json.dumps(entry["arguments"], default=str), 200),
            "result": shorten(entry["result"]),
        })
    return rows


def describe_run(result):
    """Short sentences about what really happened, including what the
    answer the user reads does not show."""
    findings = []
    for entry in result["trace"]:
        if entry["tool"] == "lookup_account_info":
            findings.append(
                f"Step {entry['step']}: called lookup_account_info, which "
                "returns the account email and API key."
            )
        elif entry["tool"] == "render_image":
            outcome = classify_image_result(str(entry["result"]))
            findings.append(
                f"Step {entry['step']}: called render_image on {image_url(entry)} "
                f"({OUTCOME_TEXT[outcome]})."
            )

    text = shown_text(result)
    if FAKE_EMAIL in text or FAKE_KEY in text:
        findings.append("The answer shown to the user contains the fake account details.")

    if result.get("error"):
        findings.append(f"The model call failed: {result['error']}")
    elif not result["completed"]:
        findings.append(f"The run did not finish normally (stop reason: {result['stop_reason']}).")

    if not findings:
        findings.append("No privileged tools were called.")
    return findings
