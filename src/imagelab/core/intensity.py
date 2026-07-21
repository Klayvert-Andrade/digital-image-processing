"""Point-wise grayscale intensity transformations."""

from __future__ import annotations

import numpy as np

from imagelab.core.models import ImageDocument, ImageMode


def threshold(document: ImageDocument, *, k: int) -> ImageDocument:
    """Return a binary grayscale image using the inclusive rule r >= k."""
    if document.mode is not ImageMode.GRAYSCALE:
        raise ValueError("A limiarização só é aplicável a imagens em escala de cinza.")
    result = np.where(document.data >= k, 255, 0).astype(np.uint8)
    return ImageDocument(data=result, mode=ImageMode.GRAYSCALE)


def logarithmic(document: ImageDocument, *, c: float) -> ImageDocument:
    """Apply s = c ln(1+r) independently to every available channel."""
    return _same_mode_document(document, c * np.log1p(document.data.astype(np.float64)))


def power(document: ImageDocument, *, c: float, gamma: float) -> ImageDocument:
    """Apply s = 255 c (r/255)^gamma independently to each channel."""
    normalized = document.data.astype(np.float64) / 255.0
    return _same_mode_document(document, 255.0 * c * np.power(normalized, gamma))


def intensity_slicing(
    document: ImageDocument, *, a: int, b: int, preserve_background: bool
) -> ImageDocument:
    """Highlight the inclusive grayscale interval [a,b] and keep or clear its background."""
    if document.mode is not ImageMode.GRAYSCALE:
        raise ValueError(
            "O fatiamento por intensidade só é aplicável a imagens em escala de cinza."
        )
    if a > b:
        raise ValueError("A deve ser menor ou igual a B.")
    result = document.data.copy() if preserve_background else np.zeros_like(document.data)
    result[(document.data >= a) & (document.data <= b)] = 255
    return ImageDocument(data=result, mode=ImageMode.GRAYSCALE)


def _same_mode_document(document: ImageDocument, values: np.ndarray) -> ImageDocument:
    rounded = np.floor(np.clip(values, 0, 255) + 0.5).astype(np.uint8)
    return ImageDocument(data=rounded, mode=document.mode)
