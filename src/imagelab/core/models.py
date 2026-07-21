"""Typed, immutable-at-the-boundary representations of accepted images."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

GrayImage: TypeAlias = NDArray[np.uint8]
RgbImage: TypeAlias = NDArray[np.uint8]
ImageArray: TypeAlias = GrayImage | RgbImage


class ImageMode(StrEnum):
    """The only image representations accepted by the application."""

    GRAYSCALE = "L"
    RGB = "RGB"

    @property
    def label(self) -> str:
        return {
            ImageMode.GRAYSCALE: "Escala de cinza (8 bits)",
            ImageMode.RGB: "RGB (24 bits)",
        }[self]


class ImageValidationError(ValueError):
    """Raised when an array does not match an ImageLab image contract."""


def infer_mode(data: ImageArray) -> ImageMode:
    """Return the mode of a valid 8-bit grayscale or RGB array."""
    if data.dtype != np.uint8:
        raise ImageValidationError("A imagem deve usar intensidades uint8 (0 a 255).")
    if data.ndim == 2:
        return ImageMode.GRAYSCALE
    if data.ndim == 3 and data.shape[2] == 3:
        return ImageMode.RGB
    raise ImageValidationError("A imagem deve ter um canal cinza ou exatamente três canais RGB.")


@dataclass(frozen=True, slots=True)
class ImageDocument:
    """An accepted image and its optional source, protected against mutation."""

    data: ImageArray
    mode: ImageMode
    source_path: Path | None = None

    def __post_init__(self) -> None:
        detected_mode = infer_mode(self.data)
        if detected_mode is not self.mode:
            raise ImageValidationError("O modo informado não corresponde aos dados da imagem.")
        if self.data.shape[0] == 0 or self.data.shape[1] == 0:
            raise ImageValidationError("A imagem precisa ter largura e altura maiores que zero.")
        self.data.setflags(write=False)

    @property
    def width(self) -> int:
        return int(self.data.shape[1])

    @property
    def height(self) -> int:
        return int(self.data.shape[0])

    @property
    def dimensions_label(self) -> str:
        return f"{self.width} × {self.height} px"
