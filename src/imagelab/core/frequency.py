"""Frequency-domain filters using the exact padded-FFT convention of ImageLab."""

from __future__ import annotations

from typing import cast

import numpy as np
from numpy.typing import NDArray

from imagelab.core.models import ImageDocument, ImageMode


def padded_shape(document: ImageDocument) -> tuple[int, int]:
    """Return the mandated doubled dimensions for frequency processing."""
    return 2 * document.height, 2 * document.width


def maximum_cutoff(document: ImageDocument) -> float:
    """Return the maximum radial cutoff expressed in padded FFT bins."""
    rows, columns = padded_shape(document)
    return float(np.hypot(rows / 2, columns / 2))


def gaussian_frequency_mask(
    shape: tuple[int, int], *, cutoff: float, high_pass: bool = False
) -> NDArray[np.float64]:
    """Build a centered Gaussian low-pass mask or its exact complement."""
    if cutoff <= 0:
        raise ValueError("A frequência de corte deve ser positiva.")
    rows, columns = shape
    vertical, horizontal = np.ogrid[:rows, :columns]
    distance_squared = (vertical - rows // 2) ** 2 + (horizontal - columns // 2) ** 2
    low_pass = np.exp(-distance_squared / (2 * cutoff**2))
    return cast(NDArray[np.float64], 1 - low_pass if high_pass else low_pass)


def gaussian_frequency_filter(
    document: ImageDocument,
    *,
    cutoff: float,
    normalized_cutoff: bool,
    high_pass: bool,
) -> ImageDocument:
    """Filter a grayscale or RGB document independently in its padded FFT domain."""
    cutoff_bins = cutoff_in_bins(document, cutoff, normalized_cutoff)
    shape = padded_shape(document)
    mask = gaussian_frequency_mask(shape, cutoff=cutoff_bins, high_pass=high_pass)
    return apply_frequency_mask(document, mask)


def cutoff_in_bins(document: ImageDocument, cutoff: float, normalized: bool) -> float:
    """Validate a user cutoff and express it in padded FFT bins."""
    maximum = maximum_cutoff(document)
    if normalized:
        if not 0 < cutoff <= 1:
            raise ValueError("A frequência normalizada deve estar no intervalo (0, 1].")
        return cutoff * maximum
    if not 0 < cutoff <= maximum:
        raise ValueError(f"A frequência de corte deve estar entre 0 e {maximum:.4f} bins.")
    return cutoff


def apply_frequency_mask(document: ImageDocument, mask: NDArray[np.float64]) -> ImageDocument:
    """Apply an already-centered padded-domain mask independently by image channel."""
    shape = padded_shape(document)
    if mask.shape != shape:
        raise ValueError("A máscara de frequência não corresponde ao padding da imagem.")
    if document.mode is ImageMode.GRAYSCALE:
        values = _filter_channel(document.data, shape, mask)
    else:
        values = np.stack(
            [_filter_channel(document.data[..., channel], shape, mask) for channel in range(3)],
            axis=-1,
        )
    return ImageDocument(data=_to_uint8(values), mode=document.mode)


def _filter_channel(
    channel: NDArray[np.uint8], shape: tuple[int, int], mask: NDArray[np.float64]
) -> NDArray[np.float64]:
    rows, columns = channel.shape
    padded = np.zeros(shape, dtype=np.float64)
    padded[:rows, :columns] = channel
    shifted = np.fft.fftshift(np.fft.fft2(padded))
    filtered = np.fft.ifft2(np.fft.ifftshift(shifted * mask)).real
    return filtered[:rows, :columns]


def _to_uint8(values: NDArray[np.float64]) -> NDArray[np.uint8]:
    return cast(NDArray[np.uint8], np.floor(np.clip(values, 0, 255) + 0.5).astype(np.uint8))
