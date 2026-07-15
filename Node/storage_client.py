"""Downloads blobs Master hands out as Google Drive links.

Kept separate from the rest of the node so swapping Master's storage backend
(MinIO/S3 later) only means changing how download_input() fetches a URL.
"""

import os
import tempfile

import gdown


def download_input(url: str, dest_dir: str = None) -> str:
    dest_dir = dest_dir or tempfile.mkdtemp(prefix="task_input_")
    dest_path = os.path.join(dest_dir, "input")
    gdown.download(url, dest_path, quiet=True, fuzzy=True)
    return dest_path
