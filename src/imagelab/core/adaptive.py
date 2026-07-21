"""Classic adaptive median filtering with the shared mirror border convention."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from imagelab.core.models import ImageDocument, ImageMode
from imagelab.core.spatial import validate_window_for_document


def adaptive_median_filter(document: ImageDocument, *, maximum_window: int) -> ImageDocument:
    """Remove impulsive noise by growing each pixel's median window when needed."""
    validate_window_for_document(maximum_window, document)
    if document.mode is ImageMode.GRAYSCALE:
        values = _adaptive_channel(document.data, maximum_window)
    else:
        values = np.stack(
            [
                _adaptive_channel(document.data[..., channel], maximum_window)
                for channel in range(3)
            ],
            axis=-1,
        )
    return ImageDocument(data=values, mode=document.mode)


def _adaptive_channel(channel: NDArray[np.uint8], maximum_window: int) -> NDArray[np.uint8]:
    padding = maximum_window // 2
    padded = np.pad(channel, padding, mode="reflect")
    result = np.empty_like(channel)
    for row in range(channel.shape[0]):
        for column in range(channel.shape[1]):
            result[row, column] = _adaptive_pixel(
                padded, row + padding, column + padding, maximum_window
            )
    return result


def _adaptive_pixel(
    padded: NDArray[np.uint8], row: int, column: int, maximum_window: int
) -> np.uint8:
    """Apply the exact Stage A / Stage B decision tree to one padded pixel."""
    for window in range(3, maximum_window + 1, 2):
        radius = window // 2
        neighborhood = padded[
            row - radius : row + radius + 1, column - radius : column + radius + 1
        ]
        minimum = int(neighborhood.min())
        maximum = int(neighborhood.max())
        median = int(np.median(neighborhood))
        if median > minimum and median < maximum:
            pixel = int(padded[row, column])
            return np.uint8(pixel if minimum < pixel < maximum else median)
    return np.uint8(median)
