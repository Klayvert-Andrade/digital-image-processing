"""Qt worker boundary that keeps CPU-bound processing outside the GUI thread."""

from __future__ import annotations

import logging
from collections.abc import Mapping

from PySide6.QtCore import QThread, Signal

from imagelab.application.processing import (
    ExecutionReport,
    ProcessController,
    ProcessValidationError,
)
from imagelab.core.models import ImageDocument

logger = logging.getLogger(__name__)


class ProcessingWorker(QThread):
    """Execute one validated catalog request and report a safe UI-facing outcome."""

    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        controller: ProcessController,
        document: ImageDocument,
        identifier: str,
        parameters: Mapping[str, object],
    ) -> None:
        super().__init__()
        self._controller = controller
        self._document = document
        self._identifier = identifier
        self._parameters = dict(parameters)

    def run(self) -> None:
        """Run outside the main Qt thread and never expose an exception to the user."""
        try:
            report = self._controller.execute(self._document, self._identifier, self._parameters)
        except ProcessValidationError as error:
            self.failed.emit(str(error))
        except Exception:
            logger.exception("Falha inesperada ao executar o processo %s", self._identifier)
            self.failed.emit(
                "Não foi possível executar o processo. Tente novamente com outros parâmetros."
            )
        else:
            self.succeeded.emit(report)


def execution_from_signal(value: object) -> ExecutionReport:
    """Narrow the Qt object signal at the single UI boundary that consumes it."""
    if not isinstance(value, ExecutionReport):
        raise TypeError("O worker retornou um resultado de processamento inválido.")
    return value
