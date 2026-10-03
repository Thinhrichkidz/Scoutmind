"""
Origin allowlist defence for render_image().

Rule: render_image() must refuse to fetch any URL whose origin is not on
config.ALLOWED_ORIGINS. An origin includes the scheme, hostname, and port.
This does not stop an allowlisted origin that logs leaked data in query
strings, or leaks in generated text that never use a tool. Those limitations
are report discussion points, not fixed by this defence.
"""

from urllib.parse import urlparse

import config


def get_origin(url):
    """Return scheme://hostname:port, or None if no valid explicit port exists."""
    try:
        parsed = urlparse(url)
        port = parsed.port
    except ValueError:
        # Malformed URLs and invalid ports cannot match an allowed origin.
        return None

    if not parsed.scheme or not parsed.hostname or port is None:
        return None
    return f"{parsed.scheme}://{parsed.hostname}:{port}"


def is_allowed(url):
    """True if the parsed origin exactly matches a configured allowed origin."""
    origin = get_origin(url)
    return origin in config.ALLOWED_ORIGINS


def check_url(url):
    """Raise ValueError if the defence is on and the url's origin isn't allowed.

    No-op when config.DEFENCE_ENABLED is False, so the undefended baseline
    behaves exactly as before.
    """
    if not config.DEFENCE_ENABLED:
        return

    if not is_allowed(url):
        origin = get_origin(url)
        if origin is None:
            message = "Blocked by defence: origin could not be determined (explicit port required)"
        else:
            message = f"Blocked by defence: origin '{origin}' is not on the allowlist"
        raise ValueError(message)
