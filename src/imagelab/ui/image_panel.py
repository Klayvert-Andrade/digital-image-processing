"""Reusable original/result image card with clear viewing controls."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from imagelab.core.models import ImageDocument
from imagelab.ui.image_canvas import ImageCanvas


class ImagePanel(QFrame):
    """Present one image, its identity and navigation without mutating the document."""

    def __init__(self, title: str, placeholder: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("imagePanel")
        self.title_label = QLabel(title)
        self.title_label.setObjectName("panelTitle")
        self.canvas = ImageCanvas(placeholder)
        self.mode_chip = _metadata_chip("Nenhuma imagem")
        self.dimensions_chip = _metadata_chip("—")
        self.fit_button = QPushButton("Ajustar")
        self.fit_button.setObjectName("secondaryButton")
        self.fit_button.setToolTip("Ajustar imagem à área visível")
        self.zoom_out_button = _zoom_button("−", "Reduzir zoom")
        self.zoom_in_button = _zoom_button("+", "Aumentar zoom")
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(25, 800)
        self.zoom_slider.setSingleStep(25)
        self.zoom_slider.setPageStep(50)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setToolTip("Ajustar zoom")
        self.zoom_label = QLabel("100%")
        self.zoom_label.setObjectName("zoomLabel")

        self.fit_button.clicked.connect(self.canvas.fit_to_view)
        self.zoom_out_button.clicked.connect(self.canvas.zoom_out)
        self.zoom_in_button.clicked.connect(self.canvas.zoom_in)
        self.zoom_slider.valueChanged.connect(self.canvas.set_zoom_percentage)
        self.canvas.zoom_changed.connect(self._set_zoom_display)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 10)
        layout.setSpacing(8)
        layout.addWidget(self.title_label)
        layout.addWidget(self.canvas, 1)

        navigation = QHBoxLayout()
        navigation.setSpacing(8)
        navigation.addWidget(self.zoom_out_button)
        navigation.addWidget(self.zoom_slider, 1)
        navigation.addWidget(self.zoom_in_button)
        navigation.addWidget(self.zoom_label)
        navigation.addWidget(self.fit_button)
        layout.addLayout(navigation)

        metadata = QHBoxLayout()
        metadata.setSpacing(8)
        metadata.addWidget(self.mode_chip)
        metadata.addWidget(self.dimensions_chip)
        metadata.addStretch()
        layout.addLayout(metadata)

    def set_document(self, document: ImageDocument | None) -> None:
        """Update the card as one visual state transition."""
        self.canvas.set_document(document)
        if document is None:
            self.mode_chip.setText("Nenhuma imagem")
            self.dimensions_chip.setText("—")
            return
        self.mode_chip.setText(document.mode.label)
        self.dimensions_chip.setText(document.dimensions_label)

    def _set_zoom_display(self, percentage: int) -> None:
        self.zoom_label.setText(f"{percentage}%")
        self.zoom_slider.blockSignals(True)
        bounded_percentage = min(
            max(percentage, self.zoom_slider.minimum()), self.zoom_slider.maximum()
        )
        self.zoom_slider.setValue(bounded_percentage)
        self.zoom_slider.blockSignals(False)


def _metadata_chip(text: str) -> QLabel:
    chip = QLabel(text)
    chip.setObjectName("metadataChip")
    return chip


def _zoom_button(text: str, tooltip: str) -> QToolButton:
    button = QToolButton()
    button.setText(text)
    button.setAccessibleName(tooltip)
    button.setToolTip(tooltip)
    button.setObjectName("zoomButton")
    return button
