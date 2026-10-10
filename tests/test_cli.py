"""The installed command explains its optional GUI dependency."""

import builtins

from host_app.gui.main import main


def test_missing_gui_extra_has_actionable_message(monkeypatch, capsys) -> None:
    original_import = builtins.__import__

    def without_qt(name, *args, **kwargs):
        if name.startswith("PyQt5"):
            raise ModuleNotFoundError("No module named 'PyQt5'", name="PyQt5")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_qt)
    assert main(["--mock"]) == 2
    assert 'pip install ".[gui,serial]"' in capsys.readouterr().err
