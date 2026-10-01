"""Central settings for ScoutMind — model, Ollama connection, and defence config."""

MODEL_NAME = "qwen3:8b"
OLLAMA_HOST = "localhost:11434"

# Context window size sent to Ollama. Its default is small; the raw HTML pages
# alone are several thousand tokens each.
NUM_CTX = 16384

# Domains render_image() is allowed to reach when DEFENCE_ENABLED is True.
ALLOWED_DOMAINS = ["127.0.0.1"]

# Master switch for the allowlist check in defence.py. Off by default so the
# undefended baseline (Goal 2) keeps working unchanged.
DEFENCE_ENABLED = False
