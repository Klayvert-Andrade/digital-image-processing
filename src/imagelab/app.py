"""Application bootstrap kept separate from the window implementation."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from imagelab.ui.main_window import MainWindow

_APPLICATION_STYLE = """
QMainWindow, QWidget {
    background: #0d1522;
    color: #edf3fc;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10.5pt;
}
QStatusBar { background: #121c2a; border-top: 1px solid #26364a; color: #c8d3e2; }
QFrame#appHeader, QFrame#imagePanel, QGroupBox {
    background: #121d2c;
    border: 1px solid #2b3b50;
    border-radius: 12px;
}
QFrame#appHeader { border-radius: 10px; }
QFrame#metricCard {
    background: #162235;
    border: 1px solid #2b3b50;
    border-radius: 9px;
}
QLabel#appTitle { font-size: 19pt; font-weight: 700; color: #f4f8ff; }
QLabel#appSubtitle, QLabel#sourceHint, QLabel#zoomLabel { color: #aab9cc; }
QLabel#panelTitle { font-size: 12pt; font-weight: 700; color: #f5f8fc; }
QLabel#metadataChip {
    background: #182537;
    border: 1px solid #2b3b50;
    border-radius: 10px;
    color: #cbd7e7;
    padding: 4px 10px;
}
QLabel#compatibilityHint { color: #7ee2a8; }
QLabel#durationLabel {
    background: #182537;
    border-radius: 9px;
    color: #cbd7e7;
    padding: 7px 10px;
}
QLabel#comparisonArrow { color: #b9c7d9; font-size: 16pt; }
QLabel#noticeLabel[severity="error"] {
    background: #3b2028;
    border: 1px solid #814152;
    border-radius: 8px;
    color: #ffd5dc;
    padding: 8px 10px;
}
QGroupBox {
    margin-top: 10px;
    padding: 12px;
    font-weight: 600;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; color: #f0f5fc; }
QPushButton, QToolButton {
    min-height: 30px;
    border-radius: 7px;
    padding: 5px 12px;
    color: #edf3fc;
}
QPushButton#primaryButton, QToolButton#primaryAction {
    background: #2873d1;
    border: 1px solid #468ae0;
    font-weight: 600;
}
QPushButton#primaryButton:hover, QToolButton#primaryAction:hover { background: #3984e3; }
QPushButton#secondaryButton, QToolButton#secondaryAction, QToolButton#zoomButton {
    background: #152235;
    border: 1px solid #3a4b61;
}
QPushButton#secondaryButton:hover, QToolButton#secondaryAction:hover, QToolButton#zoomButton:hover {
    background: #1d3049;
}
QPushButton:disabled, QToolButton:disabled {
    background: #182230;
    border-color: #293649;
    color: #728096;
}
QComboBox, QSpinBox, QDoubleSpinBox {
    background: #182537;
    border: 1px solid #33465e;
    border-radius: 7px;
    min-height: 28px;
    padding: 4px 8px;
    color: #f0f5fc;
}
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QPushButton:focus, QToolButton:focus {
    border: 2px solid #5b9dff;
}
QComboBox QAbstractItemView {
    background: #182537;
    border: 1px solid #33465e;
    color: #edf3fc;
    selection-background-color: #2873d1;
}
QSlider::groove:horizontal { background: #2a3a50; height: 4px; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #2873d1; border-radius: 2px; }
QSlider::handle:horizontal {
    background: #68a5ff; border: 1px solid #a7cbff; width: 16px;
    margin: -6px 0; border-radius: 8px;
}
QTabWidget::pane { border: 1px solid #2b3b50; border-radius: 8px; }
QTabBar::tab {
    background: #182537; color: #b9c7d9; border-radius: 6px;
    padding: 7px 12px; margin-right: 4px;
}
QTabBar::tab:selected { background: #244c82; color: white; }
QCheckBox { spacing: 6px; }
QScrollArea { background: #101923; }
QScrollBar:vertical, QScrollBar:horizontal { background: #121c2a; }
"""


def run() -> int:
    """Start the Qt event loop and return its exit status."""
    existing = QApplication.instance()
    app = existing if isinstance(existing, QApplication) else QApplication(sys.argv)
    app.setStyleSheet(_APPLICATION_STYLE)
    window = MainWindow()
    window.show()
    return app.exec()
