"""Minimal GUI composition around the hardware-independent core."""

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QVBoxLayout, QWidget

from host_app.communication.pyserial_adapter import PySerialBackend
from host_app.core.application import HostApplication
from host_app.core.config import SerialConfig
from host_app.core.errors import HostApplicationError
from host_app.gui.connection_panel import ConnectionPanel
from host_app.gui.terminal_view import TerminalView
from host_app.models.connection import ConnectionState


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Python Host Application Lab")
        self.resize(900, 560)

        self.application = HostApplication(PySerialBackend())
        self.connection_panel = ConnectionPanel()
        self.terminal = TerminalView()

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.connection_panel)
        layout.addWidget(self.terminal)
        self.setCentralWidget(central)

        self.connection_panel.refresh_requested.connect(self.refresh_ports)
        self.connection_panel.connect_requested.connect(self.connect_serial)
        self.connection_panel.disconnect_requested.connect(self.disconnect_serial)
        self.terminal.send_requested.connect(self.send_command)

        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(50)
        self.poll_timer.timeout.connect(self.poll_serial)
        self.poll_timer.start()

        self._update_state()
        self.refresh_ports()

    def refresh_ports(self) -> None:
        try:
            self.connection_panel.set_ports(self.application.available_ports())
        except HostApplicationError as exc:
            self.connection_panel.set_state(ConnectionState.ERROR, str(exc))

    def connect_serial(self, port: str, baudrate: int) -> None:
        try:
            self.connection_panel.set_state(ConnectionState.CONNECTING)
            self.application.connect(SerialConfig(port=port, baudrate=baudrate))
        except (HostApplicationError, ValueError) as exc:
            self._show_error(str(exc))
        self._update_state()

    def disconnect_serial(self) -> None:
        self.application.disconnect()
        self._update_state()

    def send_command(self, command: str) -> None:
        try:
            self.terminal.append_message(self.application.send_command(command))
        except HostApplicationError as exc:
            self._show_error(str(exc))
            self._update_state()

    def poll_serial(self) -> None:
        if self.application.state != ConnectionState.CONNECTED:
            return
        try:
            for message in self.application.poll():
                self.terminal.append_message(message)
        except HostApplicationError as exc:
            self._show_error(str(exc))
            self._update_state()

    def closeEvent(self, event: QCloseEvent | None) -> None:
        self.application.disconnect()
        if event is not None:
            event.accept()

    def _update_state(self) -> None:
        state = self.application.state
        self.connection_panel.set_state(state, self.application.connection.last_error or "")
        self.terminal.set_connected(state == ConnectionState.CONNECTED)

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Host Application", message)

