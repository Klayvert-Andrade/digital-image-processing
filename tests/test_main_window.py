from pathlib import Path
from threading import Event

import numpy as np
import pytest
from PIL import Image
from PySide6.QtCore import Qt
from pytestqt.qtbot import QtBot

from imagelab.ui.main_window import MainWindow


def test_window_starts_empty_with_export_disabled(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)

    assert not window.save_action.isEnabled()
    assert window.original_panel.mode_chip.text() == "Nenhuma imagem"
    assert window.original_panel.dimensions_chip.text() == "—"
    assert window.original_canvas.alignment() == Qt.AlignmentFlag.AlignCenter
    assert not window.metrics_view.tabs.isTabEnabled(1)


def test_window_loads_an_image_and_exposes_mode_and_dimensions(
    qtbot: QtBot, tmp_path: Path
) -> None:
    path = tmp_path / "input.png"
    Image.fromarray(np.zeros((3, 5, 3), dtype=np.uint8)).save(path)
    window = MainWindow()
    qtbot.addWidget(window)

    window.load_path(path)

    assert window.original_document is not None
    assert window.original_panel.mode_chip.text() == "RGB (24 bits)"
    assert window.original_panel.dimensions_chip.text() == "5 × 3 px"
    assert window.process_panel.source_label.text() == "Entrada: imagem original carregada."
    assert "Imagem carregada" in window.statusBar().currentMessage()
    assert not window.save_action.isEnabled()


def test_window_surfaces_load_errors_without_closing(qtbot: QtBot, tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.png"
    Image.fromarray(np.zeros((1, 1, 4), dtype=np.uint8)).save(invalid)
    window = MainWindow()
    qtbot.addWidget(window)

    window.load_path(invalid)

    assert window.original_document is None
    assert "incompatível" in window.statusBar().currentMessage().lower()
    assert not window.save_action.isEnabled()


def test_window_exports_the_displayed_result(qtbot: QtBot, tmp_path: Path) -> None:
    source = tmp_path / "input.png"
    destination = tmp_path / "result.png"
    Image.fromarray(np.array([[1, 2]], dtype=np.uint8)).save(source)
    window = MainWindow()
    qtbot.addWidget(window)
    window.load_path(source)

    window.set_result(window.original_document)
    window.export_result(destination)

    assert destination.exists()
    assert window.save_action.isEnabled()
    assert "salvo" in window.statusBar().currentMessage().lower()


def test_window_keeps_running_when_export_would_overwrite_source(
    qtbot: QtBot, tmp_path: Path
) -> None:
    source = tmp_path / "input.png"
    Image.fromarray(np.array([[1]], dtype=np.uint8)).save(source)
    window = MainWindow()
    qtbot.addWidget(window)
    window.load_path(source)
    window.set_result(window.original_document)

    window.export_result(source)

    assert "sobrescrever" in window.statusBar().currentMessage()


def test_window_executes_threshold_and_shows_metrics(qtbot: QtBot, tmp_path: Path) -> None:
    source = tmp_path / "gray.png"
    Image.fromarray(np.array([[0, 128, 255]], dtype=np.uint8)).save(source)
    window = MainWindow()
    qtbot.addWidget(window)
    window.load_path(source)
    window.process_panel.select_process("threshold")

    assert window.process_panel.execute_button.isEnabled()
    window.process_panel.set_parameter_value("k", 128)
    window.process_panel.execute_current_process()
    qtbot.waitUntil(lambda: not window._processing)

    assert window.result_document is not None
    np.testing.assert_array_equal(window.result_document.data, [[0, 255, 255]])
    assert window.save_action.isEnabled()
    assert "Duração" in window.metrics_view.duration_label.text()


def test_window_explains_that_threshold_is_unavailable_for_rgb(
    qtbot: QtBot, tmp_path: Path
) -> None:
    source = tmp_path / "rgb.png"
    Image.fromarray(np.zeros((1, 1, 3), dtype=np.uint8)).save(source)
    window = MainWindow()
    qtbot.addWidget(window)
    window.load_path(source)
    window.process_panel.select_process("threshold")

    assert not window.process_panel.execute_button.isEnabled()
    assert "incompatível" in window.process_panel.compatibility_label.text().lower()


def test_window_displays_and_exports_rgb_accessory_channels(qtbot: QtBot, tmp_path: Path) -> None:
    source = tmp_path / "rgb.png"
    destination = tmp_path / "green.png"
    Image.fromarray(np.array([[[1, 2, 3]]], dtype=np.uint8)).save(source)
    window = MainWindow()
    qtbot.addWidget(window)
    window.load_path(source)
    window.process_panel.select_process("decompose_rgb")

    window.process_panel.execute_current_process()
    qtbot.waitUntil(lambda: not window._processing)
    window.export_accessory("G", destination)

    assert window.accessory_view.count() == 3
    assert window.metrics_view.tabs.isTabEnabled(1)
    assert window.metrics_view.tabs.tabText(1) == "Resultados acessórios (3)"
    assert tuple(
        window.accessory_view.tabText(index) for index in range(window.accessory_view.count())
    ) == ("R", "G", "B")
    np.testing.assert_array_equal(np.array(Image.open(destination)), [[2]])


def test_window_warns_that_hue_is_circular(qtbot: QtBot, tmp_path: Path) -> None:
    source = tmp_path / "rgb.png"
    Image.fromarray(np.array([[[255, 0, 0]]], dtype=np.uint8)).save(source)
    window = MainWindow()
    qtbot.addWidget(window)
    window.load_path(source)
    window.process_panel.select_process("decompose_hsv")

    window.process_panel.execute_current_process()
    qtbot.waitUntil(lambda: not window._processing)

    assert "circular" in window.accessory_view.tabText(0).lower()


def test_window_names_the_rgb_sobel_result_explicitly(qtbot: QtBot, tmp_path: Path) -> None:
    source = tmp_path / "rgb-step.png"
    pixels = np.zeros((3, 3, 3), dtype=np.uint8)
    pixels[:, 2, 0] = 255
    Image.fromarray(pixels).save(source)
    window = MainWindow()
    qtbot.addWidget(window)
    window.load_path(source)
    window.process_panel.select_process("sobel")

    window.process_panel.execute_current_process()
    qtbot.waitUntil(lambda: not window._processing)

    assert window.result_title.text() == "Composição RGB das magnitudes de Sobel"


def test_window_explains_frequency_padding_convention(qtbot: QtBot, tmp_path: Path) -> None:
    source = tmp_path / "gray.png"
    Image.fromarray(np.zeros((3, 3), dtype=np.uint8)).save(source)
    window = MainWindow()
    qtbot.addWidget(window)
    window.load_path(source)
    window.process_panel.select_process("gaussian_low_pass_frequency")

    assert "wraparound" in window.process_panel.description_label.text()


def test_window_keeps_essential_controls_responsive_while_worker_runs(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "gray.png"
    Image.fromarray(np.zeros((3, 3), dtype=np.uint8)).save(source)
    window = MainWindow()
    qtbot.addWidget(window)
    window.load_path(source)
    window.process_panel.select_process("threshold")
    started = Event()
    release = Event()
    original_execute = window._controller.execute

    def delayed_execute(*args: object, **kwargs: object) -> object:
        started.set()
        assert release.wait(1)
        return original_execute(*args, **kwargs)

    monkeypatch.setattr(window._controller, "execute", delayed_execute)
    window.process_panel.execute_current_process()
    qtbot.waitUntil(started.is_set)

    assert window._processing
    assert not window.process_panel.execute_button.isEnabled()
    assert window.process_panel.execute_button.text() == "Processando…"
    assert not window.process_panel.process_combo.isEnabled()
    assert not window.open_action.isEnabled()
    release.set()
    qtbot.waitUntil(lambda: not window._processing)
    assert window.open_action.isEnabled()
    assert window.process_panel.execute_button.text() == "Processar"


def test_window_exposes_a_clear_action_hierarchy(qtbot: QtBot, tmp_path: Path) -> None:
    source = tmp_path / "gray.png"
    Image.fromarray(np.zeros((3, 3), dtype=np.uint8)).save(source)
    window = MainWindow()
    qtbot.addWidget(window)
    window.load_path(source)

    assert window.process_panel.execute_button.objectName() == "primaryButton"
    assert window.process_panel.reset_button.objectName() == "secondaryButton"
    assert "Compatível" in window.process_panel.compatibility_label.text()


def test_process_controls_restore_declared_defaults(qtbot: QtBot, tmp_path: Path) -> None:
    source = tmp_path / "gray.png"
    Image.fromarray(np.zeros((7, 7), dtype=np.uint8)).save(source)
    window = MainWindow()
    qtbot.addWidget(window)
    window.load_path(source)
    window.process_panel.select_process("gaussian_blur")
    window.process_panel.set_parameter_value("window", 7)
    window.process_panel.set_parameter_value("sigma", 3.5)

    window.process_panel.restore_defaults()

    assert window.process_panel._parameter_values() == {"window": 3, "sigma": 1.0}


def test_window_handles_worker_validation_errors_without_exposing_tracebacks(
    qtbot: QtBot, tmp_path: Path
) -> None:
    source = tmp_path / "gray.png"
    Image.fromarray(np.zeros((3, 3), dtype=np.uint8)).save(source)
    window = MainWindow()
    qtbot.addWidget(window)
    window.load_path(source)

    window._execute_process("threshold", {"k": 999})
    qtbot.waitUntil(lambda: not window._processing)

    assert "Limiar" in window.notice_label.text()
    assert "traceback" not in window.notice_label.text().lower()
    assert window.open_action.isEnabled()


def test_window_runs_five_distinct_processes_without_reloading(
    qtbot: QtBot, tmp_path: Path
) -> None:
    source = tmp_path / "gradient.png"
    Image.fromarray(np.tile(np.arange(7, dtype=np.uint8) * 30, (7, 1))).save(source)
    window = MainWindow()
    qtbot.addWidget(window)
    window.load_path(source)

    requests = (
        ("threshold", {"k": 100}),
        ("logarithmic", {"c": 255 / np.log(256)}),
        ("power", {"c": 1.0, "gamma": 0.5}),
        ("gaussian_blur", {"window": 3, "sigma": 1.0}),
        ("sobel", {"window": 3}),
    )
    original = window.original_document
    for identifier, values in requests:
        window.process_panel.select_process(identifier)
        for key, value in values.items():
            window.process_panel.set_parameter_value(key, value)
        window.process_panel.execute_current_process()
        qtbot.waitUntil(lambda: not window._processing)
        assert window.result_document is not None

    assert window.original_document is original
