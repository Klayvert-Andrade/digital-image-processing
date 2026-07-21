"""Structured outputs shared by all image-processing operations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from imagelab.core.models import ImageDocument


@dataclass(frozen=True, slots=True)
class ProcessResult:
    """A primary exportable image plus optional named supporting images."""

    primary: ImageDocument
    accessories: Mapping[str, ImageDocument] = field(default_factory=dict)
    primary_label: str = "Resultado"

    def __post_init__(self) -> None:
        object.__setattr__(self, "accessories", MappingProxyType(dict(self.accessories)))
