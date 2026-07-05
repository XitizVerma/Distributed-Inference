from config import STORAGE_BACKEND
from storage.google_drive import GoogleDriveStorage

_BACKENDS = {
    "google_drive": GoogleDriveStorage,
}

_instance = None


def get_storage():
    """Returns the configured storage backend (singleton).

    Backend is chosen by the STORAGE_BACKEND env var, so swapping Google Drive
    for MinIO/S3 later only means adding a class here and flipping the env var
    — nothing else in the codebase should import a backend directly.
    """
    global _instance
    if _instance is None:
        backend_cls = _BACKENDS.get(STORAGE_BACKEND)
        if not backend_cls:
            raise ValueError(f"Unknown STORAGE_BACKEND: {STORAGE_BACKEND!r}")
        _instance = backend_cls()
    return _instance
