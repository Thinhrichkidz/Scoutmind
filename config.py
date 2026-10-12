"""Central settings for ScoutMind — model, Ollama connection, and defence config."""

import threading

MODEL_NAME = "qwen3:8b"
OLLAMA_HOST = "localhost:11434"

# Context window size sent to Ollama. Its default is small; the raw HTML pages
# alone are several thousand tokens each.
NUM_CTX = 16384

# Origins (scheme, host, and explicit port) allowed when DEFENCE_ENABLED is True.
ALLOWED_ORIGINS = ["http://127.0.0.1:8001"]

# Master switch for the allowlist check in defence.py. Off by default so the
# undefended baseline (Goal 2) keeps working unchanged.
DEFENCE_ENABLED = False

# Which defence layers apply when DEFENCE_ENABLED is True. Both default to on, so
# turning the master switch on behaves exactly as before; the Streamlit sidebar
# can switch one layer off to show what each layer does on its own.
ALLOWLIST_ENABLED = True  # origin allowlist on render_image (defence.check_url)
FILTER_ENABLED = True  # output filter on the summary (defence.filter_summary)

# DEFENCE_ENABLED is one setting for the whole process. Hold this lock while
# changing it (or the two layer flags above) AND while the agent runs, so two runs (for example two browser
# tabs of the Streamlit app) cannot change it under each other.
DEFENCE_LOCK = threading.Lock()
