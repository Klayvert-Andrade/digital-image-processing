"""Comparable image metrics displayed for each execution."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

import numpy as np

from imagelab.core.models import ImageDocument, ImageMode


@dataclass(frozen=True, slots=True)
class ChannelMetrics:
    """Basic descriptive statistics for one image channel."""

    minimum: int
    maximum: int
    mean: float
    standard_deviation: float


@dataclass(frozen=True, slots=True)
class ImageMetrics:
    """Dimensions, representation and channel-wise statistics of an image."""

    width: int
    height: int
    mode: ImageMode
    channels: Mapping[str, ChannelMetrics]


def calculate_metrics(document: ImageDocument) -> ImageMetrics:
    """Calculate metrics without changing the source document."""
    if document.mode is ImageMode.GRAYSCALE:
        channels = {"Cinza": _channel_metrics(document.data)}
    else:
        channels = {
            name: _channel_metrics(document.data[..., index])
            for index, name in enumerate(("R", "G", "B"))
        }
    return ImageMetrics(
        width=document.width,
        height=document.height,
        mode=document.mode,
        channels=MappingProxyType(channels),
    )


def _channel_metrics(channel: np.ndarray) -> ChannelMetrics:
    return ChannelMetrics(
        minimum=int(channel.min()),
        maximum=int(channel.max()),
        mean=float(channel.mean()),
        standard_deviation=float(channel.std()),
    )
