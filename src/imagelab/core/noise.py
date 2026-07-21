"""Deterministic-testable additive and impulsive noise generators."""

from __future__ import annotations

from typing import Literal, cast

import numpy as np
from numpy.typing import NDArray

from imagelab.core.models import ImageDocument

ImpulseKind = Literal["salt", "pepper", "salt_pepper"]


def gaussian_noise(
    document: ImageDocument,
    *,
    mu: float,
    sigma: float,
    rng: np.random.Generator | None = None,
) -> ImageDocument:
    """Add independent Gaussian samples to each grayscale or RGB component."""
    if not -255 <= mu <= 255:
        raise ValueError("A média do ruído deve estar entre -255 e 255.")
    if not 0 <= sigma <= 255:
        raise ValueError("O desvio padrão do ruído deve estar entre 0 e 255.")
    generator = rng or np.random.default_rng()
    samples = generator.normal(mu, sigma, size=document.data.shape)
    return ImageDocument(
        data=_to_uint8(document.data.astype(np.float64) + samples), mode=document.mode
    )


def impulse_noise(
    document: ImageDocument,
    *,
    density: float,
    kind: ImpulseKind,
    salt_proportion: float = 0.5,
    rng: np.random.Generator | None = None,
) -> ImageDocument:
    """Change an exact number of distinct pixel coordinates to salt and/or pepper."""
    _validate_probability(density, "A densidade")
    if kind == "salt_pepper":
        _validate_probability(salt_proportion, "A proporção de sal")
    generator = rng or np.random.default_rng()
    total_pixels = document.height * document.width
    affected = _rounded_count(density, total_pixels)
    flat_coordinates = generator.choice(total_pixels, size=affected, replace=False)
    rows, columns = np.unravel_index(flat_coordinates, (document.height, document.width))
    noisy = document.data.copy()
    if kind == "salt":
        noisy[rows, columns] = 255
    elif kind == "pepper":
        noisy[rows, columns] = 0
    elif kind == "salt_pepper":
        salt_count = _rounded_count(salt_proportion, affected)
        noisy[rows[:salt_count], columns[:salt_count]] = 255
        noisy[rows[salt_count:], columns[salt_count:]] = 0
    else:
        raise ValueError(f"Tipo de ruído impulsivo desconhecido: {kind}.")
    return ImageDocument(data=noisy, mode=document.mode)


def _rounded_count(fraction: float, total: int) -> int:
    return int(np.floor(fraction * total + 0.5))


def _validate_probability(value: float, label: str) -> None:
    if not 0 <= value <= 1:
        raise ValueError(f"{label} deve estar entre 0 e 1.")


def _to_uint8(values: np.ndarray) -> NDArray[np.uint8]:
    return cast(NDArray[np.uint8], np.floor(np.clip(values, 0, 255) + 0.5).astype(np.uint8))
