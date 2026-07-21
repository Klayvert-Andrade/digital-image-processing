"""Reusable spatial-filter primitives with the project's mirror border policy."""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

import numpy as np
from numpy.typing import NDArray

from imagelab.core.models import ImageDocument


def gaussian_kernel(*, window: int, sigma: float) -> NDArray[np.float64]:
    """Sample and normalize the project-standard 2D Gaussian kernel."""
    _validate_window(window)
    if sigma <= 0:
        raise ValueError("Sigma deve ser positivo.")
    coordinates = np.arange(window, dtype=np.float64) - window // 2
    x, y = np.meshgrid(coordinates, coordinates)
    kernel = np.exp(-(x**2 + y**2) / (2 * sigma**2))
    return cast(NDArray[np.float64], kernel / kernel.sum())


def gaussian_blur(document: ImageDocument, *, window: int, sigma: float) -> ImageDocument:
    """Blur grayscale or RGB images independently by channel with mirror borders."""
    return ImageDocument(
        data=_to_uint8(gaussian_blur_values(document, window=window, sigma=sigma)),
        mode=document.mode,
    )


def gaussian_blur_values(
    document: ImageDocument, *, window: int, sigma: float
) -> NDArray[np.float64]:
    """Return Gaussian-smoothed values before export rounding and clipping."""
    validate_window_for_document(window, document)
    kernel = gaussian_kernel(window=window, sigma=sigma)
    return _apply_per_channel(document.data, lambda channel: _convolve_mirror(channel, kernel))


def order_filter(document: ImageDocument, *, window: int, operation: str) -> ImageDocument:
    """Apply median, minimum or maximum statistics over mirror-extended square windows."""
    validate_window_for_document(window, document)
    reducers = {"median": _window_median, "minimum": _window_minimum, "maximum": _window_maximum}
    try:
        reducer = reducers[operation]
    except KeyError as error:
        raise ValueError(f"Filtro de ordem desconhecido: {operation}.") from error
    filtered = _apply_per_channel(
        document.data, lambda channel: _reduce_mirror_window(channel, window, reducer)
    )
    return ImageDocument(data=_to_uint8(filtered), mode=document.mode)


def _apply_per_channel(
    data: np.ndarray, operation: Callable[[NDArray[np.float64]], NDArray[np.float64]]
) -> NDArray[np.float64]:
    floating = cast(NDArray[np.float64], data.astype(np.float64))
    if floating.ndim == 2:
        return operation(floating)
    return cast(
        NDArray[np.float64],
        np.stack([operation(floating[..., index]) for index in range(3)], axis=-1),
    )


def _to_uint8(values: np.ndarray) -> NDArray[np.uint8]:
    return cast(NDArray[np.uint8], np.floor(np.clip(values, 0, 255) + 0.5).astype(np.uint8))


def _convolve_mirror(
    channel: NDArray[np.float64], kernel: NDArray[np.float64]
) -> NDArray[np.float64]:
    padding = kernel.shape[0] // 2
    padded = np.pad(channel, padding, mode="reflect")
    windows = np.lib.stride_tricks.sliding_window_view(padded, kernel.shape)
    return cast(NDArray[np.float64], np.einsum("ijkl,kl->ij", windows, kernel))


def _reduce_mirror_window(
    channel: NDArray[np.float64],
    window: int,
    reducer: Callable[[NDArray[np.float64]], NDArray[np.float64]],
) -> NDArray[np.float64]:
    padding = window // 2
    windows = np.lib.stride_tricks.sliding_window_view(
        np.pad(channel, padding, mode="reflect"), (window, window)
    )
    return reducer(windows)


def _window_median(windows: NDArray[np.float64]) -> NDArray[np.float64]:
    return cast(NDArray[np.float64], np.median(windows, axis=(-2, -1)))


def _window_minimum(windows: NDArray[np.float64]) -> NDArray[np.float64]:
    return cast(NDArray[np.float64], np.min(windows, axis=(-2, -1)))


def _window_maximum(windows: NDArray[np.float64]) -> NDArray[np.float64]:
    return cast(NDArray[np.float64], np.max(windows, axis=(-2, -1)))


def _validate_window(window: int) -> None:
    if window < 3 or window > 31 or window % 2 == 0:
        raise ValueError("A janela deve ser ímpar e estar entre 3 e 31.")


def validate_window_for_document(window: int, document: ImageDocument) -> None:
    _validate_window(window)
    if window > min(document.height, document.width):
        raise ValueError("A janela não pode exceder as dimensões da imagem.")
