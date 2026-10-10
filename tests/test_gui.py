"""Real Qt widgets exercised with the original in-memory serial backend."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PyQt5")
from PyQt5.QtWidgets import QApplication

from host_app.communication.mock_serial import MockSerialBackend
from host_app.core.errors import CommunicationError
from host_app.gui.connection_panel import ConnectionPanel
from host_app.gui.main import DemoMockSerialBackend
from host_app.gui.main_window import MainWindow
from host_app.models.connection import ConnectionState
from host_app.models.device import SerialPortInfo


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    instance = QApplication.instance()
    return instance if isinstance(instance, QApplication) else QApplication([])


def test_port_refresh_preserves_real_id_and_manual_entry(qt_app: QApplication) -> None:
    panel = ConnectionPanel()
    port = SerialPortInfo("COM7", "Test port", "FAKE")
    panel.set_ports([port])
    panel.set_ports([port])
    assert panel.port_combo.count() == 1
    assert panel.port_combo.currentData() == "COM7"
    selected: list[tuple[str, int]] = []
    panel.connect_requested.connect(lambda name, baud: selected.append((name, baud)))
    panel._on_connect_clicked()
    assert selected[-1] == ("COM7", 115200)

    panel.port_combo.setEditText("COM9")
    panel.set_ports([port])
    assert panel.port_combo.count() == 2
    panel._on_connect_clicked()
    assert selected[-1] == ("COM9", 115200)
    panel.close()


def test_mock_gui_connect_send_receive_disconnect_reconnect(qt_app: QApplication) -> None:
    backend = MockSerialBackend()
    window = MainWindow(backend)
    window.show()
    qt_app.processEvents()
    assert window.connection_panel.port_combo.currentData() == "MOCK0"
    window.connection_panel._on_connect_clicked()
    assert window.application.state == ConnectionState.CONNECTED
    assert window.application.config is not None
    assert window.application.config.read_timeout == 0.0
    window.send_command("status")
    assert backend.sent_data == (b"status\r\n",)
    backend.queue_receive(b"ready\n")
    window.poll_serial()
    assert "[RX] ready" in window.terminal.output.toPlainText()
    window.disconnect_serial()
    assert window.application.state == ConnectionState.DISCONNECTED
    window.connection_panel._on_connect_clicked()
    assert window.application.state == ConnectionState.CONNECTED
    window.close()
    assert not backend.is_open


def test_gui_disconnect_exception_is_reported_and_recoverable(qt_app: QApplication) -> None:
    class CloseFailsOnce(MockSerialBackend):
        failures = 1

        def close(self) -> None:
            super().close()
            if self.failures:
                self.failures -= 1
                raise CommunicationError("close failed")

    backend = CloseFailsOnce()
    window = MainWindow(backend)
    errors: list[str] = []
    window._show_error = errors.append  # type: ignore[method-assign]
    window.connect_serial("MOCK0", 115200)
    window.disconnect_serial()
    assert errors == ["close failed"]
    assert window.application.state == ConnectionState.DISCONNECTED
    window.connect_serial("MOCK0", 115200)
    assert window.application.state == ConnectionState.CONNECTED
    window.close()


def test_visible_mock_demo_replies_without_hardware(qt_app: QApplication) -> None:
    backend = DemoMockSerialBackend()
    window = MainWindow(backend)
    window.connect_serial("MOCK0", 115200)
    window.send_command("status")
    window.poll_serial()
    assert "[RX] MOCK ACK: status" in window.terminal.output.toPlainText()
    window.close()
