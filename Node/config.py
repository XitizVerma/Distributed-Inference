import os
import socket

from dotenv import load_dotenv

load_dotenv()

MASTER_URL = os.environ.get("MASTER_URL", "http://localhost:8000")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
# How long Ollama keeps a model loaded in memory after a request. "0" unloads it
# immediately after each response (model loads on-demand per prompt, frees memory
# while idle); a duration like "5m" keeps it warm for faster back-to-back requests
# at the cost of holding memory during idle time.
OLLAMA_KEEP_ALIVE = os.environ.get("OLLAMA_KEEP_ALIVE", "0")
HOSTNAME = socket.gethostname()
NODE_NAME = os.environ.get("NODE_NAME") or HOSTNAME
HEARTBEAT_INTERVAL_SECONDS = int(os.environ.get("HEARTBEAT_INTERVAL_SECONDS", "5"))
