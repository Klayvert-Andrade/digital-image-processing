"""Discrete grayscale histogram processing and visualization."""

from __future__ import annotations

import numpy as np

from imagelab.core.models import ImageDocument, ImageMode
from imagelab.core.results import ProcessResult


def histogram_counts(image: np.ndarray) -> np.ndarray:
    """Count every uint8 pixel in a fixed 256-level histogram."""
    return np.bincount(image.ravel(), minlength=256).astype(np.int64)


def equalization_lut(counts: np.ndarray) -> np.ndarray:
    """Create T(r)=floor(255*CDF(r)+0.5), without CDF-min subtraction."""
    total = int(counts.sum())
    if total == 0:
        raise ValueError("O histograma não pode ser vazio.")
    cdf = np.cumsum(counts, dtype=np.float64) / total
    return np.floor(255 * cdf + 0.5).astype(np.uint8)


def histogram_equalization(document: ImageDocument) -> ProcessResult:
    """Equalize a grayscale image and provide before/after histogram images."""
    if document.mode is not ImageMode.GRAYSCALE:
        raise ValueError("A equalização de histograma só é aplicável a imagens em escala de cinza.")
    before = histogram_counts(document.data)
    result = equalization_lut(before)[document.data]
    after = histogram_counts(result)
    return ProcessResult(
        primary=ImageDocument(data=result, mode=ImageMode.GRAYSCALE),
        accessories={
            "Histograma antes": _histogram_image(before),
            "Histograma depois": _histogram_image(after),
        },
    )


def _histogram_image(counts: np.ndarray) -> ImageDocument:
    height = 160
    image = np.full((height, 256, 3), 24, dtype=np.uint8)
    maximum = int(counts.max())
    if maximum:
        bar_heights = np.floor(counts * (height - 12) / maximum).astype(int)
        for column, bar_height in enumerate(bar_heights):
            if bar_height:
                image[height - 1 - bar_height : height - 1, column] = (103, 210, 255)
    image[-1, :, :] = 160
    return ImageDocument(data=image, mode=ImageMode.RGB)
