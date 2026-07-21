"""Display and export auxiliary images produced by a process."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTabWidget, QVBoxLayout, QWidget

from imagelab.core.models import ImageDocument
from imagelab.ui.image_canvas import ImageCanvas

AccessoryExportHandler = Callable[[str, ImageDocument], None]


class AccessoryView(QTabWidget):
    """Tabs for named image results, intentionally separate from the primary result."""

    def set_accessories(
        self, accessories: Mapping[str, ImageDocument], on_export: AccessoryExportHandler
    ) -> None:
        """Replace tabs atomically with the current execution's auxiliary images."""
        self.clear()
        for name, document in accessories.items():
            tab = QWidget()
            layout = QVBoxLayout(tab)
            canvas = ImageCanvas(f"Canal {name}")
            canvas.set_document(document)
            export_button = QPushButton(f"Salvar canal {name}…")
            export_button.clicked.connect(
                lambda _=False, channel=name, image=document: on_export(channel, image)
            )
            actions = QHBoxLayout()
            actions.addStretch()
            actions.addWidget(export_button)
            layout.addWidget(canvas, 1)
            layout.addLayout(actions)
            self.addTab(tab, _tab_label(name))


def _tab_label(name: str) -> str:
    return "H — Matiz (grandeza circular)" if name == "H" else name
