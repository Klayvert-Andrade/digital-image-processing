"""The main ImageLab desktop window."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStatusBar,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from imagelab.application.processing import ProcessController
from imagelab.core.catalog import PROCESS_CATALOG
from imagelab.core.models import ImageDocument
from imagelab.infrastructure.image_io import ImageLoadError, ImageSaveError, load_png, save_png
from imagelab.ui.accessory_view import AccessoryView
from imagelab.ui.image_panel import ImagePanel
from imagelab.ui.metrics_view import MetricsView
from imagelab.ui.process_panel import ProcessPanel
from imagelab.ui.processing_worker import ProcessingWorker, execution_from_signal


class MainWindow(QMainWindow):
    """Own presentation state while keeping image algorithms outside the UI."""

    def __init__(self) -> None:
        super().__init__()
        self.original_document: ImageDocument | None = None
        self.result_document: ImageDocument | None = None
        self._accessories: dict[str, ImageDocument] = {}
        self._processing = False
        self._worker: ProcessingWorker | None = None
        self._controller = ProcessController(PROCESS_CATALOG)

        self.setWindowTitle("ImageLab PDI")
        self.resize(1280, 720)
        self.setMinimumSize(900, 600)

        self.open_action = QAction("Abrir PNG…", self)
        self.open_action.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton)
        )
        self.open_action.triggered.connect(self.choose_image)
        self.save_action = QAction("Salvar resultado…", self)
        self.save_action.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)
        )
        self.save_action.triggered.connect(self.choose_export_path)
        self.save_action.setEnabled(False)
        self._create_content()

        status_bar = QStatusBar(self)
        status_bar.showMessage("Selecione uma imagem PNG para começar.")
        self.setStatusBar(status_bar)

    def _create_content(self) -> None:
        root = QWidget(self)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(12)

        root_layout.addWidget(self._create_header())

        self.notice_label = QLabel("")
        self.notice_label.setObjectName("noticeLabel")
        self.notice_label.setWordWrap(True)
        self.notice_label.setVisible(False)
        root_layout.addWidget(self.notice_label)

        images_layout = QHBoxLayout()
        images_layout.setSpacing(16)
        self.original_panel = ImagePanel(
            "Imagem original", "Carregue um PNG em escala de cinza ou RGB."
        )
        self.result_panel = ImagePanel("Resultado", "Selecione um processo para gerar o resultado.")
        self.original_canvas = self.original_panel.canvas
        self.result_canvas = self.result_panel.canvas
        self.result_title = self.result_panel.title_label
        images_layout.addWidget(self.original_panel, 1)
        images_layout.addWidget(self.result_panel, 1)
        root_layout.addLayout(images_layout, 1)

        controls_layout = QHBoxLayout()
        self.process_panel = ProcessPanel(PROCESS_CATALOG, self._execute_process)
        self.metrics_view = MetricsView()
        controls_layout.addWidget(self.process_panel, 1)
        controls_layout.addWidget(self.metrics_view, 2)
        root_layout.addLayout(controls_layout)

        self.accessory_view = AccessoryView()
        self.metrics_view.set_accessory_view(self.accessory_view)
        self.setCentralWidget(root)

    def _create_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("appHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 12, 16, 12)
        title_block = QVBoxLayout()
        title_block.setSpacing(1)
        title = QLabel("ImageLab PDI")
        title.setObjectName("appTitle")
        subtitle = QLabel("Processamento Digital de Imagens")
        subtitle.setObjectName("appSubtitle")
        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        layout.addLayout(title_block)
        layout.addStretch()
        open_button = _action_button(self.open_action, "secondaryAction")
        save_button = _action_button(self.save_action, "primaryAction")
        layout.addWidget(open_button)
        layout.addWidget(save_button)
        return header

    def choose_image(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "Abrir imagem PNG", "", "Imagens PNG (*.png)"
        )
        if filename:
            self.load_path(Path(filename))

    def load_path(self, path: Path) -> None:
        """Load an image selected by the user, preserving a usable window on failure."""
        try:
            document = load_png(path)
        except ImageLoadError as error:
            self._show_error(str(error))
            return

        self.original_document = document
        self.set_result(None)
        self._set_accessories({})
        self.process_panel.set_image(document)
        self.metrics_view.clear()
        self.original_panel.set_document(document)
        self._clear_notice()
        self.statusBar().showMessage("Imagem carregada com sucesso.")

    def _execute_process(self, identifier: str, parameters: Mapping[str, object]) -> None:
        if self.original_document is None or self._processing:
            return
        self._processing = True
        self.process_panel.set_processing(True)
        self.open_action.setEnabled(False)
        self.statusBar().showMessage("Processando imagem original…")
        worker = ProcessingWorker(self._controller, self.original_document, identifier, parameters)
        self._worker = worker
        worker.succeeded.connect(self._show_execution)
        worker.failed.connect(self._show_error)
        worker.finished.connect(self._finish_processing)
        worker.start()

    def _show_execution(self, payload: object) -> None:
        execution = execution_from_signal(payload)
        self.set_result(execution.result.primary, label=execution.result.primary_label)
        self._set_accessories(execution.result.accessories)
        self.metrics_view.show_execution(execution)
        self._clear_notice()
        self.statusBar().showMessage(f"Processamento concluído em {execution.duration_ms:.2f} ms.")

    def _finish_processing(self) -> None:
        """Release the worker only after its thread has actually stopped."""
        worker = self._worker
        self._worker = None
        self._processing = False
        self.open_action.setEnabled(True)
        if worker is not None:
            worker.deleteLater()
        self.process_panel.set_processing(False)

    def set_result(self, document: ImageDocument | None, *, label: str = "Resultado") -> None:
        """Display the current exportable result; used by the processing controller."""
        self.result_document = document
        self.result_title.setText(label)
        self.result_panel.set_document(document)
        self.save_action.setEnabled(document is not None)

    def _set_accessories(self, accessories: Mapping[str, ImageDocument]) -> None:
        self._accessories = dict(accessories)
        self.accessory_view.set_accessories(accessories, self._choose_accessory_export)
        self.metrics_view.set_accessory_count(len(accessories))

    def _choose_accessory_export(self, name: str, document: ImageDocument) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self, f"Salvar canal {name}", f"canal-{name}.png", "Imagens PNG (*.png)"
        )
        if filename:
            self.export_accessory(name, Path(filename), document=document)

    def export_accessory(
        self, name: str, path: Path, *, document: ImageDocument | None = None
    ) -> None:
        """Export one named accessory without altering the original or result state."""
        image = document or self._accessories.get(name)
        if image is None:
            self._show_error(f"Resultado acessório indisponível: {name}.")
            return
        try:
            source_path = self.original_document.source_path if self.original_document else None
            save_png(path, image, protected_source=source_path)
        except (ImageSaveError, ValueError) as error:
            self._show_error(str(error))
            return
        self._clear_notice()
        self.statusBar().showMessage(f"Canal {name} salvo com sucesso.")

    def choose_export_path(self) -> None:
        if self.result_document is None:
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar resultado", "resultado.png", "Imagens PNG (*.png)"
        )
        if filename:
            self.export_result(Path(filename))

    def export_result(self, path: Path) -> None:
        """Export the displayed result and surface recoverable write errors."""
        if self.result_document is None:
            return
        try:
            source_path = self.original_document.source_path if self.original_document else None
            save_png(path, self.result_document, protected_source=source_path)
        except (ImageSaveError, ValueError) as error:
            self._show_error(str(error))
            return
        self._clear_notice()
        self.statusBar().showMessage("Resultado salvo com sucesso.")

    def _show_error(self, message: str) -> None:
        self.notice_label.setText(message)
        self.notice_label.setProperty("severity", "error")
        self.notice_label.style().unpolish(self.notice_label)
        self.notice_label.style().polish(self.notice_label)
        self.notice_label.setVisible(True)
        self.statusBar().showMessage(message)

    def _clear_notice(self) -> None:
        self.notice_label.clear()
        self.notice_label.setVisible(False)


def _action_button(action: QAction, object_name: str) -> QToolButton:
    button = QToolButton()
    button.setDefaultAction(action)
    button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
    button.setObjectName(object_name)
    return button
