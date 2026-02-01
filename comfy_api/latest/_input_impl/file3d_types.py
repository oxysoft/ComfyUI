from __future__ import annotations

import io
import shutil
from pathlib import Path
from typing import IO, Union


class File3D:
    """
    Class representing a 3D file from a file path or binary stream.

    Supports both disk-backed (file path) and memory-backed (BytesIO) storage,
    similar to VideoFromFile. Disk-backed mode is more memory-efficient for
    large 3D models.
    """

    def __init__(self, path: Union[str, IO[bytes]], file_format: str = ""):
        """
        Initialize the File3D object.

        Args:
            path: Either a file path (str) or a binary stream (BytesIO/IO[bytes])
                  containing the 3D file data.
            file_format: The format of the 3D file (e.g., 'glb', 'fbx', 'obj').
                        If not provided and path is a string, it will be inferred
                        from the file extension.
        """
        self._path = path
        self._format = file_format or self._infer_format()

    def _infer_format(self) -> str:
        """Infer file format from path if it's a string."""
        if isinstance(self._path, str):
            return Path(self._path).suffix.lstrip(".").lower()
        return ""

    @property
    def format(self) -> str:
        """Get the file format."""
        return self._format

    @format.setter
    def format(self, value: str) -> None:
        """Set the file format."""
        self._format = value.lstrip(".").lower() if value else ""

    @property
    def is_disk_backed(self) -> bool:
        """Check if the file is stored on disk (vs in memory)."""
        return isinstance(self._path, str)

    def get_source(self) -> Union[str, IO[bytes]]:
        """
        Get the underlying source for streaming.

        Returns:
            Either a file path (str) or a BytesIO object.
            For disk-backed files, returns the path directly to avoid memory copy.
        """
        if isinstance(self._path, str):
            return self._path
        # Reset stream position for IO objects
        if hasattr(self._path, "seek"):
            self._path.seek(0)
        return self._path

    @property
    def data(self) -> io.BytesIO:
        """
        Get the file data as a BytesIO object.

        For disk-backed files, this reads the entire file into memory.
        The returned BytesIO is positioned at the beginning.
        """
        if isinstance(self._path, str):
            # Read from disk
            with open(self._path, "rb") as f:
                result = io.BytesIO(f.read())
            return result
        # Already a stream - reset position and return
        if hasattr(self._path, "seek"):
            self._path.seek(0)
        if isinstance(self._path, io.BytesIO):
            return self._path
        # For other IO types, wrap in BytesIO
        return io.BytesIO(self._path.read())

    def save_to(self, path: str) -> str:
        """
        Save the 3D file to disk.

        For disk-backed files, this uses an efficient file copy.
        For memory-backed files, this writes the buffer to disk.

        Args:
            path: Destination file path.

        Returns:
            The destination path.
        """
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(self._path, str):
            # Disk-backed: efficient copy
            if Path(self._path).resolve() != dest.resolve():
                shutil.copy2(self._path, dest)
        else:
            # Memory-backed: write bytes
            if hasattr(self._path, "seek"):
                self._path.seek(0)
            with open(dest, "wb") as f:
                f.write(self._path.read())

        return str(dest)

    def get_bytes(self) -> bytes:
        """
        Get the raw bytes of the 3D file.

        For disk-backed files, this reads the entire file.
        For memory-backed files, this returns the buffer contents.
        """
        if isinstance(self._path, str):
            return Path(self._path).read_bytes()
        if hasattr(self._path, "seek"):
            self._path.seek(0)
        return self._path.read()

    def __repr__(self) -> str:
        if isinstance(self._path, str):
            return f"File3D(path={self._path!r}, format={self._format!r})"
        return f"File3D(<stream>, format={self._format!r})"
