"""Central settings for ScoutMind — model, Ollama connection, and defence config."""

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
