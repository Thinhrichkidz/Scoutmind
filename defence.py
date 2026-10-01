"""
Domain allowlist defence for render_image().

Rule: render_image() must refuse to fetch any URL whose domain is not on
config.ALLOWED_DOMAINS. This does not stop an attacker who controls an
allowlisted domain (see README/report for the CDN-abuse variant), and it
does nothing for leaks that never touch a tool call at all (the text-only
variant) — both are discussed in the report, not fixed here.
"""

from urllib.parse import urlparse

import config


def get_domain(url):
    """Extract the hostname from a URL, e.g. 'http://127.0.0.1:8000/log' -> '127.0.0.1'."""
    return urlparse(url).hostname


def is_allowed(url):
    """True if url's domain is on config.ALLOWED_DOMAINS."""
    domain = get_domain(url)
    return domain in config.ALLOWED_DOMAINS


def check_url(url):
    """Raise ValueError if the defence is on and the url's domain isn't allowed.

    No-op when config.DEFENCE_ENABLED is False, so the undefended baseline
    behaves exactly as before.
    """
    if not config.DEFENCE_ENABLED:
        return

    if not is_allowed(url):
        raise ValueError(
            f"Blocked by defence: domain '{get_domain(url)}' is not on the allowlist"
        )
