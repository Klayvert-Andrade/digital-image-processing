"""Scannable comparison of execution metrics and accessory results."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from imagelab.application.processing import ExecutionReport
from imagelab.core.metrics import ImageMetrics

_EMPTY_METRICS_MESSAGE = "Execute um processo para comparar a imagem original e o resultado."


class MetricsView(QGroupBox):
    """Show an at-a-glance comparison while keeping channel detail available."""

    def __init__(self) -> None:
        super().__init__("Métricas relevantes")
        self.tabs = QTabWidget()
        self.metrics_tab = QWidget()
        self.accessories_tab: QWidget | None = None
        self.content_label = QLabel(_EMPTY_METRICS_MESSAGE)
        self.content_label.setObjectName("metricsEmptyState")
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet("color: #aab9cc;")
        self.original_card = MetricCard("Original", "#62a7ff")
        self.result_card = MetricCard("Resultado", "#76e59d")
        self.duration_label = QLabel("")
        self.duration_label.setObjectName("durationLabel")
        self.duration_label.setVisible(False)

        metrics_layout = QVBoxLayout(self.metrics_tab)
        metrics_layout.setContentsMargins(10, 10, 10, 10)
        metrics_layout.setSpacing(10)
        metrics_layout.addWidget(self.content_label)

        comparison = QHBoxLayout()
        comparison.setSpacing(10)
        comparison.addWidget(self.original_card, 1)
        self.comparison_arrow = QLabel("→")
        self.comparison_arrow.setObjectName("comparisonArrow")
        comparison.addWidget(self.comparison_arrow)
        comparison.addWidget(self.result_card, 1)
        metrics_layout.addLayout(comparison)
        metrics_layout.addWidget(self.duration_label)
        self._set_metrics_visible(False)

        self.tabs.addTab(self.metrics_tab, "Métricas")
        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)

    def set_accessory_view(self, accessory_view: QWidget) -> None:
        """Attach the accessory surface as a secondary, initially disabled tab."""
        self.accessories_tab = accessory_view
        self.tabs.addTab(accessory_view, "Resultados acessórios")
        self.set_accessory_count(0)

    def set_accessory_count(self, count: int) -> None:
        """Expose accessory availability without distracting when there are none."""
        if self.accessories_tab is None:
            return
        index = self.tabs.indexOf(self.accessories_tab)
        self.tabs.setTabEnabled(index, count > 0)
        suffix = f" ({count})" if count else ""
        self.tabs.setTabText(index, f"Resultados acessórios{suffix}")
        if count == 0:
            self.tabs.setCurrentWidget(self.metrics_tab)

    def show_execution(self, execution: ExecutionReport) -> None:
        """Render comparable metrics for one completed execution."""
        self._set_metrics_visible(True)
        _set_card_metrics(self.original_card, execution.original_metrics)
        _set_card_metrics(self.result_card, execution.result_metrics)
        self.duration_label.setText(f"Duração do processamento: {execution.duration_ms:.2f} ms")
        self.duration_label.setVisible(True)

    def clear(self) -> None:
        """Restore the empty state after loading a new original image."""
        self.content_label.setText(_EMPTY_METRICS_MESSAGE)
        self.duration_label.clear()
        self.duration_label.setVisible(False)
        self._set_metrics_visible(False)
        self.set_accessory_count(0)

    def _set_metrics_visible(self, visible: bool) -> None:
        self.content_label.setVisible(not visible)
        self.original_card.setVisible(visible)
        self.result_card.setVisible(visible)
        self.comparison_arrow.setVisible(visible)


class MetricCard(QFrame):
    """One compact, explicit metric summary card."""

    def __init__(self, title: str, accent: str) -> None:
        super().__init__()
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(5)
        heading = QLabel(title)
        heading.setStyleSheet(f"color: {accent}; font-weight: 700;")
        self.summary = QLabel("")
        self.summary.setObjectName("metricSummary")
        self.summary.setWordWrap(True)
        self.details = QLabel("")
        self.details.setObjectName("metricDetails")
        self.details.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(self.summary)
        layout.addWidget(self.details)


def _set_card_metrics(card: MetricCard, metrics: ImageMetrics) -> None:
    card.summary.setText(f"{metrics.mode.label} · {metrics.width} × {metrics.height} px")
    card.details.setText(_format_channel_metrics(metrics))


def _format_channel_metrics(metrics: ImageMetrics) -> str:
    return "\n".join(
        f"{name}: mín. {values.minimum}, máx. {values.maximum} · "
        f"média {values.mean:.2f}, desvio {values.standard_deviation:.2f}"
        for name, values in metrics.channels.items()
    )
