"""Butterworth masks built on the shared ImageLab frequency pipeline."""

from __future__ import annotations

from typing import cast

import numpy as np
from numpy.typing import NDArray

from imagelab.core.frequency import apply_frequency_mask, cutoff_in_bins, padded_shape
from imagelab.core.models import ImageDocument


def butterworth_mask(
    shape: tuple[int, int], *, cutoff: float, order: int, high_pass: bool = False
) -> NDArray[np.float64]:
    """Build a numerically stable centered Butterworth low- or high-pass mask."""
    _validate_order(order)
    if cutoff <= 0:
        raise ValueError("A frequência de corte deve ser positiva.")
    rows, columns = shape
    vertical, horizontal = np.ogrid[:rows, :columns]
    distance = np.hypot(vertical - rows // 2, horizontal - columns // 2)
    with np.errstate(divide="ignore"):
        exponent = 2 * order * np.log(distance / cutoff)
    low_pass = np.exp(-np.logaddexp(0.0, exponent))
    return cast(NDArray[np.float64], 1 - low_pass if high_pass else low_pass)


def butterworth_frequency_filter(
    document: ImageDocument,
    *,
    cutoff: float,
    normalized_cutoff: bool,
    order: int,
    high_pass: bool,
) -> ImageDocument:
    """Filter a document using the shared padded FFT flow and Butterworth mask."""
    cutoff_bins = cutoff_in_bins(document, cutoff, normalized_cutoff)
    mask = butterworth_mask(
        padded_shape(document), cutoff=cutoff_bins, order=order, high_pass=high_pass
    )
    return apply_frequency_mask(document, mask)


def _validate_order(order: int) -> None:
    if isinstance(order, bool) or order < 1 or order > 20:
        raise ValueError("A ordem Butterworth deve ser um inteiro entre 1 e 20.")
