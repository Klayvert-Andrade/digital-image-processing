"""Application-level process execution, timing and metric collection."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from time import perf_counter

from imagelab.core.catalog import CatalogValidationError, ProcessCatalog
from imagelab.core.metrics import ImageMetrics, calculate_metrics
from imagelab.core.models import ImageDocument
from imagelab.core.results import ProcessResult


class ProcessValidationError(ValueError):
    """A user-facing validation failure before or during process execution."""


@dataclass(frozen=True, slots=True)
class ExecutionReport:
    """Everything the UI needs after a successful process execution."""

    result: ProcessResult
    original_metrics: ImageMetrics
    result_metrics: ImageMetrics
    duration_ms: float


class ProcessController:
    """Execute a cataloged process against an immutable original image."""

    def __init__(self, catalog: ProcessCatalog) -> None:
        self._catalog = catalog

    def execute(
        self, original: ImageDocument, identifier: str, parameters: Mapping[str, object]
    ) -> ExecutionReport:
        """Validate, execute once, and collect comparable metrics and duration."""
        try:
            definition = self._catalog.get(identifier)
            if original.mode not in definition.compatible_modes:
                raise ProcessValidationError(
                    f"{definition.label} não é compatível com {original.mode.label}."
                )
            validated = definition.validate_parameters(parameters)
        except CatalogValidationError as error:
            raise ProcessValidationError(str(error)) from error

        started_at = perf_counter()
        try:
            result = definition.executor(original, validated)
        except ValueError as error:
            raise ProcessValidationError(str(error)) from error
        duration_ms = (perf_counter() - started_at) * 1_000
        return ExecutionReport(
            result=result,
            original_metrics=calculate_metrics(original),
            result_metrics=calculate_metrics(result.primary),
            duration_ms=duration_ms,
        )
