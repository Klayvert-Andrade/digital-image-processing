import pytest

import imagelab.__main__ as entrypoint
import imagelab.app as app_module


def test_run_bootstraps_window_and_returns_qt_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    created: dict[str, object] = {}

    class FakeApplication:
        @staticmethod
        def instance() -> None:
            return None

        def __init__(self, arguments: list[str]) -> None:
            created["arguments"] = arguments

        def exec(self) -> int:
            return 7

    class FakeWindow:
        def show(self) -> None:
            created["shown"] = True

    monkeypatch.setattr(app_module, "QApplication", FakeApplication)
    monkeypatch.setattr(app_module, "MainWindow", FakeWindow)
    FakeApplication.setStyleSheet = lambda _self, stylesheet: created.update(stylesheet=stylesheet)

    assert app_module.run() == 7
    assert created["shown"] is True
    assert "QMainWindow" in str(created["stylesheet"])


def test_main_exits_with_application_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(entrypoint, "run", lambda: 3)

    with pytest.raises(SystemExit, match="3"):
        entrypoint.main()
