"""Zoomable, pannable image display widgets without image mutation."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import QEvent, QObject, QPointF, Qt, Signal
from PySide6.QtGui import QImage, QMouseEvent, QPixmap, QResizeEvent, QWheelEvent
from PySide6.QtWidgets import QLabel, QScrollArea
from typing_extensions import override

from imagelab.core.models import ImageDocument, ImageMode


class ImageCanvas(QScrollArea):
    """Display an image with fit, zoom and drag-to-pan navigation."""

    zoom_changed = Signal(int)

    def __init__(self, placeholder: str) -> None:
        super().__init__()
        self._placeholder = placeholder
        self._source_pixmap: QPixmap | None = None
        self._zoom = 1.0
        self._fit_mode = True
        self._drag_position: QPointF | None = None
        self._image_label = QLabel(placeholder)
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setWordWrap(True)
        self._image_label.setCursor(Qt.CursorShape.OpenHandCursor)
        self._image_label.installEventFilter(self)
        self.setWidget(self._image_label)
        self.setWidgetResizable(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(260, 220)
        self.setStyleSheet(
            "QScrollArea { background: #171b22; border: 1px solid #394150; border-radius: 8px; }"
            "QLabel { color: #b8c2d1; padding: 12px; }"
        )

    def alignment(self) -> Qt.AlignmentFlag:
        """Expose the content alignment for callers that need its presentation contract."""
        return self._image_label.alignment()

    def set_document(self, document: ImageDocument | None) -> None:
        """Show a document, or restore the neutral empty state."""
        if document is None:
            self._source_pixmap = None
            self._image_label.clear()
            self._image_label.setText(self._placeholder)
            self._image_label.adjustSize()
            self.zoom_changed.emit(100)
            return
        self._source_pixmap = QPixmap.fromImage(_to_qimage(document))
        self._image_label.setText("")
        self.fit_to_view()

    def fit_to_view(self) -> None:
        """Fit the source image to the viewport while preserving its aspect ratio."""
        if self._source_pixmap is None or self.viewport().size().isEmpty():
            return
        source_size = self._source_pixmap.size()
        viewport_size = self.viewport().size()
        scale = min(
            viewport_size.width() / source_size.width(),
            viewport_size.height() / source_size.height(),
        )
        self._fit_mode = True
        self._set_zoom(scale)

    def zoom_in(self) -> None:
        """Increase display magnification by one predictable step."""
        self._fit_mode = False
        self._set_zoom(self._zoom * 1.25)

    def zoom_out(self) -> None:
        """Decrease display magnification without allowing a degenerate canvas."""
        self._fit_mode = False
        self._set_zoom(self._zoom / 1.25)

    def set_zoom_percentage(self, percentage: int) -> None:
        """Set an explicit zoom value requested by the navigation slider."""
        self._fit_mode = False
        self._set_zoom(percentage / 100)

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self._fit_mode:
            self.fit_to_view()

    @override
    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            elif event.angleDelta().y() < 0:
                self.zoom_out()
            event.accept()
            return
        super().wheelEvent(event)

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self._image_label:
            if event.type() is QEvent.Type.MouseButtonPress:
                mouse_event = _mouse_event(event)
                if mouse_event.button() is Qt.MouseButton.LeftButton:
                    self._drag_position = mouse_event.position()
                    self._image_label.setCursor(Qt.CursorShape.ClosedHandCursor)
                    return True
            elif event.type() is QEvent.Type.MouseMove and self._drag_position is not None:
                mouse_event = _mouse_event(event)
                delta = mouse_event.position() - self._drag_position
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() - round(delta.x())
                )
                self.verticalScrollBar().setValue(
                    self.verticalScrollBar().value() - round(delta.y())
                )
                self._drag_position = mouse_event.position()
                return True
            elif event.type() is QEvent.Type.MouseButtonRelease and self._drag_position is not None:
                self._drag_position = None
                self._image_label.setCursor(Qt.CursorShape.OpenHandCursor)
                return True
        return super().eventFilter(watched, event)

    def _set_zoom(self, zoom: float) -> None:
        if self._source_pixmap is None:
            return
        self._zoom = max(0.05, min(zoom, 32.0))
        size = self._source_pixmap.size() * self._zoom
        self._image_label.setPixmap(
            self._source_pixmap.scaled(
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self._image_label.resize(size)
        self.zoom_changed.emit(round(self._zoom * 100))


def _mouse_event(event: QEvent) -> QMouseEvent:
    if not isinstance(event, QMouseEvent):
        raise TypeError("Evento de navegação de imagem inválido.")
    return event


def _to_qimage(document: ImageDocument) -> QImage:
    data = np.ascontiguousarray(document.data)
    image_format = (
        QImage.Format.Format_Grayscale8
        if document.mode is ImageMode.GRAYSCALE
        else QImage.Format.Format_RGB888
    )
    image = QImage(data.data, document.width, document.height, data.strides[0], image_format)
    return image.copy()
