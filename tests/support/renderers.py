"""Local document-renderer double used only by synthetic tests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path


class SyntheticPdfium:
    def __init__(
        self,
        writer: Callable[[Path], object],
        *,
        expected_page_index: int,
        expected_scale: float,
    ) -> None:
        self.writer = writer
        self.expected_page_index = expected_page_index
        self.expected_scale = expected_scale

    def PdfDocument(self, _path: str) -> _Document:  # noqa: N802 - mirrors optional SDK
        return _Document(self)


class _Document:
    def __init__(self, owner: SyntheticPdfium) -> None:
        self.owner = owner

    def __getitem__(self, index: int) -> _Page:
        assert index == self.owner.expected_page_index
        return _Page(self.owner)


class _Page:
    def __init__(self, owner: SyntheticPdfium) -> None:
        self.owner = owner

    def render(self, *, scale: float) -> _Bitmap:
        assert scale == self.owner.expected_scale
        return _Bitmap(self.owner.writer)


class _Bitmap:
    def __init__(self, writer: Callable[[Path], object]) -> None:
        self.writer = writer

    def to_pil(self) -> _Image:
        return _Image(self.writer)


class _Image:
    def __init__(self, writer: Callable[[Path], object]) -> None:
        self.writer = writer

    def save(self, destination: Path, *, format: str) -> None:
        assert format == "PNG"
        self.writer(Path(destination))
