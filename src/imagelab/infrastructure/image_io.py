"""Strict PNG input and output boundaries for ImageLab."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

from imagelab.core.models import ImageDocument, ImageMode


class ImageLoadError(ValueError):
    """A user-facing error raised when a selected file is not an accepted PNG."""


class ImageSaveError(ValueError):
    """A user-facing error raised when an image cannot be exported as PNG."""


_SUPPORTED_PIL_MODES: dict[str, ImageMode] = {
    "L": ImageMode.GRAYSCALE,
    "RGB": ImageMode.RGB,
}


def load_png(path: Path) -> ImageDocument:
    """Load an 8-bit L or RGB PNG without coercing its mode or channel order."""
    if path.suffix.lower() != ".png":
        raise ImageLoadError(
            "Selecione um arquivo PNG em escala de cinza de 8 bits ou RGB de 24 bits."
        )

    try:
        with Image.open(path) as image:
            image.load()
            if image.format != "PNG":
                raise ImageLoadError("O arquivo selecionado não é um PNG válido.")
            mode = _SUPPORTED_PIL_MODES.get(image.mode)
            if mode is None:
                raise ImageLoadError(
                    "PNG incompatível: use escala de cinza de 8 bits ou RGB de 24 bits, sem alfa."
                )
            data = np.array(image, dtype=np.uint8, copy=True)
    except ImageLoadError:
        raise
    except (OSError, UnidentifiedImageError) as error:
        raise ImageLoadError(f"Não foi possível abrir a imagem: {error}") from error

    return ImageDocument(data=data, mode=mode, source_path=path.resolve())


def save_png(path: Path, document: ImageDocument, *, protected_source: Path | None = None) -> None:
    """Export a document to a distinct PNG path, surfacing I/O failures clearly."""
    if path.suffix.lower() != ".png":
        raise ImageSaveError("O resultado deve ser salvo com a extensão .png.")
    if protected_source is not None and path.resolve() == protected_source.resolve():
        raise ValueError(
            "Para preservar a imagem original, escolha outro nome de arquivo sem sobrescrever."
        )

    try:
        Image.fromarray(document.data).save(path, format="PNG")
    except OSError as error:
        raise ImageSaveError(f"Não foi possível salvar o resultado: {error}") from error
