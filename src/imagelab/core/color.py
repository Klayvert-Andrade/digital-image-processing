"""RGB and conventional HSV channel decompositions."""

from __future__ import annotations

from types import MappingProxyType

import numpy as np

from imagelab.core.models import ImageDocument, ImageMode
from imagelab.core.results import ProcessResult


def decompose_rgb(document: ImageDocument) -> ProcessResult:
    """Extract R, G and B exactly as three 8-bit grayscale images."""
    _require_rgb(document)
    channels = {
        name: ImageDocument(data=document.data[..., index].copy(), mode=ImageMode.GRAYSCALE)
        for index, name in enumerate(("R", "G", "B"))
    }
    return ProcessResult(primary=channels["R"], accessories=MappingProxyType(channels))


def decompose_hsv(document: ImageDocument) -> ProcessResult:
    """Compute conventional HSV channels and map each deterministically to 8 bits."""
    _require_rgb(document)
    normalized = document.data.astype(np.float64) / 255.0
    red, green, blue = (normalized[..., index] for index in range(3))
    maximum = np.maximum(np.maximum(red, green), blue)
    minimum = np.minimum(np.minimum(red, green), blue)
    delta = maximum - minimum

    hue = np.zeros_like(maximum)
    chromatic = delta > 0
    red_maximum = chromatic & (maximum == red)
    green_maximum = chromatic & (maximum == green)
    blue_maximum = chromatic & (maximum == blue)
    hue[red_maximum] = np.mod((green[red_maximum] - blue[red_maximum]) / delta[red_maximum], 6)
    hue[green_maximum] = (blue[green_maximum] - red[green_maximum]) / delta[green_maximum] + 2
    hue[blue_maximum] = (red[blue_maximum] - green[blue_maximum]) / delta[blue_maximum] + 4
    hue = np.mod(hue * 60, 360)

    saturation = np.divide(delta, maximum, out=np.zeros_like(maximum), where=maximum > 0)
    channels = {
        "H": _gray_document(np.floor(hue * 255 / 360 + 0.5)),
        "S": _gray_document(np.floor(saturation * 255 + 0.5)),
        "V": _gray_document(np.floor(maximum * 255 + 0.5)),
    }
    return ProcessResult(primary=channels["H"], accessories=MappingProxyType(channels))


def _gray_document(values: np.ndarray) -> ImageDocument:
    return ImageDocument(data=np.clip(values, 0, 255).astype(np.uint8), mode=ImageMode.GRAYSCALE)


def _require_rgb(document: ImageDocument) -> None:
    if document.mode is not ImageMode.RGB:
        raise ValueError("Esta decomposição é aplicável somente a imagens RGB.")
