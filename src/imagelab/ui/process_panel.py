"""Catalog-driven process selection and parameter controls."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from imagelab.core.catalog import ParameterKind, ParameterSpec, ProcessCatalog
from imagelab.core.models import ImageDocument, ImageMode

ProcessRequestHandler = Callable[[str, Mapping[str, object]], None]


class ProcessPanel(QGroupBox):
    """A reusable UI projection of the canonical process catalog."""

    def __init__(self, catalog: ProcessCatalog, on_execute: ProcessRequestHandler) -> None:
        super().__init__("Processo")
        self._catalog = catalog
        self._on_execute = on_execute
        self._mode: ImageMode | None = None
        self._controls: dict[str, QWidget] = {}
        self._parameters: tuple[ParameterSpec, ...] = ()
        self._parameter_identifier: str | None = None
        self._processing = False

        self.process_combo = QComboBox()
        self.source_label = QLabel("Entrada: carregue uma imagem PNG.")
        self.source_label.setObjectName("sourceHint")
        self.compatibility_label = QLabel("Carregue uma imagem para habilitar os processos.")
        self.compatibility_label.setObjectName("compatibilityHint")
        self.compatibility_label.setWordWrap(True)
        self.description_label = QLabel("")
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: #aab4c2;")
        self.parameter_form = QFormLayout()
        self.reset_button = QPushButton("Restaurar padrões")
        self.reset_button.setObjectName("secondaryButton")
        self.reset_button.clicked.connect(self.restore_defaults)
        self.execute_button = QPushButton("Processar")
        self.execute_button.setObjectName("primaryButton")
        self.execute_button.clicked.connect(self.execute_current_process)

        layout = QVBoxLayout(self)
        layout.addWidget(self.process_combo)
        layout.addWidget(self.source_label)
        layout.addWidget(self.compatibility_label)
        layout.addWidget(self.description_label)
        layout.addLayout(self.parameter_form)
        actions = QHBoxLayout()
        actions.addWidget(self.reset_button)
        actions.addWidget(self.execute_button)
        layout.addLayout(actions)

        self.process_combo.currentIndexChanged.connect(self._on_selection_changed)
        self._populate_catalog()
        self._refresh()

    def set_image(self, document: ImageDocument | None) -> None:
        """Refresh per-process compatibility for the currently loaded original image."""
        self._mode = document.mode if document is not None else None
        self.source_label.setText(
            "Entrada: imagem original carregada."
            if document is not None
            else "Entrada: carregue uma imagem PNG."
        )
        self._populate_catalog()
        self._refresh()

    def set_processing(self, processing: bool) -> None:
        """Make the currently visible controls reflect worker activity."""
        self._processing = processing
        self._refresh()

    def set_parameter_value(self, key: str, value: object) -> None:
        """Set a parameter control for an interaction test or programmatic preset."""
        control = self._controls.get(key)
        if isinstance(control, QSpinBox) and isinstance(value, int):
            control.setValue(value)
        elif isinstance(control, QDoubleSpinBox) and isinstance(value, (int, float)):
            control.setValue(float(value))
        elif isinstance(control, QCheckBox) and isinstance(value, bool):
            control.setChecked(value)
        else:
            raise KeyError(f"Valor inválido para o parâmetro: {key}.")

    def select_process(self, identifier: str) -> None:
        """Select a catalog entry explicitly, including an incompatible one for inspection."""
        for index in range(self.process_combo.count()):
            if self.process_combo.itemData(index, Qt.ItemDataRole.UserRole) == identifier:
                self.process_combo.setCurrentIndex(index)
                self._refresh()
                return
        raise KeyError(f"Processo desconhecido: {identifier}.")

    def execute_current_process(self) -> None:
        """Submit selected process metadata and UI values through the injected boundary."""
        if not self.execute_button.isEnabled():
            return
        identifier = self._selected_identifier()
        if identifier is None:
            return
        self._on_execute(identifier, self._parameter_values())

    def restore_defaults(self) -> None:
        """Restore only the controls for the currently selected process."""
        for parameter in self._parameters:
            self.set_parameter_value(parameter.key, parameter.default)

    def _populate_catalog(self) -> None:
        selected_identifier = self._selected_identifier()
        model = QStandardItemModel(self.process_combo)
        selected_index: int | None = None
        first_compatible_index: int | None = None
        current_category: str | None = None
        for definition in self._catalog.all():
            if definition.category != current_category:
                category = QStandardItem(definition.category)
                category.setEnabled(False)
                category.setData(None, Qt.ItemDataRole.UserRole)
                model.appendRow(category)
                current_category = definition.category
            item = QStandardItem(f"   {definition.label}")
            item.setData(definition.identifier, Qt.ItemDataRole.UserRole)
            compatible = self._mode is not None and self._mode in definition.compatible_modes
            item.setEnabled(compatible)
            entry_index = model.rowCount()
            model.appendRow(item)
            if compatible and first_compatible_index is None:
                first_compatible_index = entry_index
            if definition.identifier == selected_identifier and compatible:
                selected_index = entry_index
        if selected_index is None:
            selected_index = first_compatible_index if first_compatible_index is not None else 0
        self.process_combo.blockSignals(True)
        self.process_combo.setModel(model)
        self.process_combo.setCurrentIndex(selected_index)
        self.process_combo.blockSignals(False)

    def _on_selection_changed(self, _: int) -> None:
        self._refresh()

    def _refresh(self) -> None:
        identifier = self._selected_identifier()
        if identifier is None:
            self.execute_button.setEnabled(False)
            self.reset_button.setEnabled(False)
            self.compatibility_label.setText("Nenhum processo disponível.")
            return
        definition = self._catalog.get(identifier)
        if identifier != self._parameter_identifier:
            self._build_parameter_controls(definition.parameters)
            self._parameter_identifier = identifier
        self.description_label.setText(definition.description)
        self.description_label.setVisible(bool(definition.description))
        if self._mode is None:
            self.execute_button.setEnabled(False)
            self.reset_button.setEnabled(False)
            self.compatibility_label.setText("Carregue uma imagem para habilitar os processos.")
        elif self._mode not in definition.compatible_modes:
            self.execute_button.setEnabled(False)
            self.reset_button.setEnabled(False)
            self.compatibility_label.setText(
                f"{definition.label} é incompatível com {self._mode.label}."
            )
        else:
            self.execute_button.setEnabled(not self._processing)
            self.reset_button.setEnabled(not self._processing)
            self.compatibility_label.setText(f"Compatível · {self._mode.label}")
        self.process_combo.setEnabled(not self._processing)
        for control in self._controls.values():
            control.setEnabled(not self._processing)
        self.execute_button.setText("Processando…" if self._processing else "Processar")

    def _build_parameter_controls(self, parameters: tuple[ParameterSpec, ...]) -> None:
        while self.parameter_form.rowCount() > 0:
            self.parameter_form.removeRow(0)
        self._controls.clear()
        self._parameters = parameters
        for parameter in parameters:
            control = self._make_control(parameter)
            self._controls[parameter.key] = control
            suffix = f" ({parameter.unit})" if parameter.unit else ""
            self.parameter_form.addRow(f"{parameter.label}{suffix}", control)

    def _make_control(self, parameter: ParameterSpec) -> QWidget:
        if parameter.kind is ParameterKind.INTEGER:
            integer_control = QSpinBox()
            integer_control.setRange(int(parameter.minimum or 0), int(parameter.maximum or 100))
            integer_control.setValue(int(parameter.default))
            return integer_control
        if parameter.kind is ParameterKind.NUMBER:
            number_control = QDoubleSpinBox()
            number_control.setDecimals(6)
            number_control.setRange(float(parameter.minimum or 0), float(parameter.maximum or 100))
            number_control.setKeyboardTracking(False)
            number_control.setValue(float(parameter.default))
            return number_control
        if parameter.kind is ParameterKind.BOOLEAN:
            boolean_control = QCheckBox()
            boolean_control.setChecked(bool(parameter.default))
            return boolean_control
        raise ValueError(f"O controle para {parameter.kind} ainda não foi implementado.")

    def _selected_identifier(self) -> str | None:
        value = self.process_combo.currentData(Qt.ItemDataRole.UserRole)
        return value if isinstance(value, str) else None

    def _parameter_values(self) -> dict[str, object]:
        values: dict[str, object] = {}
        for key, control in self._controls.items():
            if isinstance(control, (QSpinBox, QDoubleSpinBox)):
                values[key] = control.value()
            elif isinstance(control, QCheckBox):
                values[key] = control.isChecked()
            else:
                raise RuntimeError(f"Controle não suportado para {key}.")
        return values
