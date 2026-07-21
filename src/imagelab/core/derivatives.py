"""Sharpening and derivative operations with explicit numeric conventions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

import cv2
import numpy as np
from numpy.typing import NDArray

from imagelab.core.models import ImageDocument, ImageMode
from imagelab.core.results import ProcessResult
from imagelab.core.spatial import gaussian_blur_values


@dataclass(frozen=True, slots=True)
class SobelResponse:
    """Floating-point Sobel components before export clipping."""

    horizontal: NDArray[np.float64]
    vertical: NDArray[np.float64]
    magnitude: NDArray[np.float64]


def unsharp_mask(
    document: ImageDocument, *, window: int, sigma: float, gain: float
) -> ImageDocument:
    """Add a gain-weighted Gaussian detail mask to the source image."""
    if gain < 0:
        raise ValueError("O ganho de aguçamento deve ser não negativo.")
    source = _floating(document.data)
    blurred = gaussian_blur_values(document, window=window, sigma=sigma)
    return _export(source + gain * (source - blurred), document.mode)


def laplacian_response(document: ImageDocument, *, window: int) -> NDArray[np.float64]:
    """Return the signed CV_64F Laplacian response for every image channel."""
    _validate_derivative_window(window)
    return _per_channel_cv(
        document,
        lambda channel: cast(
            NDArray[np.float64],
            cv2.Laplacian(channel, cv2.CV_64F, ksize=window, borderType=cv2.BORDER_REFLECT_101),
        ),
    )


def laplacian(document: ImageDocument, *, window: int) -> ProcessResult:
    """Enhance an image with the signed Laplacian and expose its adjusted view."""
    response = laplacian_response(document, window=window)
    enhanced = _export(_floating(document.data) - response, document.mode)
    return ProcessResult(
        primary=enhanced,
        accessories={"Laplaciano ajustado": _export(_adjust(response), document.mode)},
    )


def sobel_response(document: ImageDocument, *, window: int) -> SobelResponse:
    """Return signed Sobel components and L1 magnitude in floating point."""
    _validate_derivative_window(window)
    horizontal = _per_channel_cv(
        document,
        lambda channel: cast(
            NDArray[np.float64],
            cv2.Sobel(channel, cv2.CV_64F, 1, 0, ksize=window, borderType=cv2.BORDER_REFLECT_101),
        ),
    )
    vertical = _per_channel_cv(
        document,
        lambda channel: cast(
            NDArray[np.float64],
            cv2.Sobel(channel, cv2.CV_64F, 0, 1, ksize=window, borderType=cv2.BORDER_REFLECT_101),
        ),
    )
    return SobelResponse(
        horizontal=horizontal,
        vertical=vertical,
        magnitude=np.abs(horizontal) + np.abs(vertical),
    )


def sobel(document: ImageDocument, *, window: int) -> ProcessResult:
    """Export clipped L1 Sobel magnitude, keeping RGB channels independent."""
    response = sobel_response(document, window=window)
    label = (
        "Composição RGB das magnitudes de Sobel"
        if document.mode is ImageMode.RGB
        else "Magnitude de Sobel"
    )
    return ProcessResult(primary=_export(response.magnitude, document.mode), primary_label=label)


def _per_channel_cv(
    document: ImageDocument,
    operation: Callable[[NDArray[np.uint8]], NDArray[np.float64]],
) -> NDArray[np.float64]:
    """Run an OpenCV derivative independently on R, G and B when present."""
    if document.mode is ImageMode.GRAYSCALE:
        return operation(document.data)
    return cast(
        NDArray[np.float64],
        np.stack([operation(document.data[..., index]) for index in range(3)], axis=-1),
    )


def _adjust(response: NDArray[np.float64]) -> NDArray[np.float64]:
    minimum = float(response.min())
    maximum = float(response.max())
    if maximum == minimum:
        return np.zeros_like(response)
    return 255 * (response - minimum) / (maximum - minimum)


def _export(values: NDArray[np.float64], mode: ImageMode) -> ImageDocument:
    pixels = cast(NDArray[np.uint8], np.floor(np.clip(values, 0, 255) + 0.5).astype(np.uint8))
    return ImageDocument(data=pixels, mode=mode)


def _floating(values: np.ndarray) -> NDArray[np.float64]:
    return cast(NDArray[np.float64], values.astype(np.float64))


def _validate_derivative_window(window: int) -> None:
    if window not in {3, 5, 7}:
        raise ValueError("A janela de derivada deve ser 3, 5 ou 7.")
