from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    def upload(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        """Uploads a blob and returns a URL a worker or the Streamlit UI can fetch it from."""

    @abstractmethod
    def delete(self, reference: str) -> None:
        """Deletes a previously uploaded object, given the reference upload() returned."""
