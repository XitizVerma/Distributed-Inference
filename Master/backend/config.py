import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "distributed_inference")

# true = require TLS to MySQL (no server cert verification); false = plain TCP.
DB_SSL_MODE = os.environ.get("DB_SSL_MODE", "false").strip().lower() == "true"

DATABASE_URL = (
    f"mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

DB_CONNECT_ARGS = {"ssl": {}} if DB_SSL_MODE else {}

HEARTBEAT_TIMEOUT_SECONDS = int(os.environ.get("HEARTBEAT_TIMEOUT_SECONDS", "30"))
METRICS_RETENTION_HOURS = int(os.environ.get("METRICS_RETENTION_HOURS", "24"))

STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "google_drive")
GOOGLE_SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "google_service_account.json")
GOOGLE_DRIVE_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")

# Browser-based frontends (frontend2) call this API directly from JS, so their
# origin must be allow-listed for CORS. Comma-separated list of full origins
# (scheme + host + port, no path). Defaults cover the Vite dev server.
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]
