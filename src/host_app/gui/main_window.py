"""Minimal GUI composition around the hardware-independent core."""

from PyQt5.QtCore import QIODevice, QSaveFile, QTimer
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from host_app.communication.interface import SerialBackend
from host_app.communication.pyserial_adapter import PySerialBackend
from host_app.core.application import HostApplication
from host_app.core.config import SerialConfig
from host_app.core.errors import HostApplicationError
from host_app.gui.connection_panel import ConnectionPanel
from host_app.gui.terminal_view import TerminalView
from host_app.models.connection import ConnectionState


class MainWindow(QMainWindow):
    def __init__(self, backend: SerialBackend | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Python Host Application Lab")
        self.resize(900, 560)

        self.application = HostApplication(backend if backend is not None else PySerialBackend())
        self.connection_panel = ConnectionPanel()
        self.terminal = TerminalView()

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.connection_panel)
        layout.addWidget(self.terminal)
        self.setCentralWidget(central)

        self.export_action = QAction("Export transcript…", self)
        self.export_action.triggered.connect(self._choose_transcript_path)
        menu_bar = self.menuBar()
        if menu_bar is None:
            raise RuntimeError("Qt menu bar is unavailable")
        file_menu = menu_bar.addMenu("File")
        if file_menu is None:
            raise RuntimeError("Qt File menu is unavailable")
        file_menu.addAction(self.export_action)

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
        else:
            self._update_state()

    def connect_serial(self, port: str, baudrate: int) -> None:
        try:
            self.connection_panel.set_state(ConnectionState.CONNECTING)
            # GUI polling is non-blocking; the core's default timeout remains
            # available to non-GUI callers.
            self.application.connect(SerialConfig(port=port, baudrate=baudrate, read_timeout=0.0))
        except (HostApplicationError, ValueError) as exc:
            self._show_error(str(exc))
        self._update_state()

    def disconnect_serial(self) -> None:
        try:
            self.application.disconnect()
        except HostApplicationError as exc:
            self._show_error(str(exc))
        finally:
            self._update_state()

    def send_command(self, command: str) -> None:
        try:
            self.terminal.append_message(self.application.send_command(command))
            self.terminal.command.clear()
        except HostApplicationError as exc:
            self._show_error(str(exc))
            self._update_state()

    def _choose_transcript_path(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export transcript", "session.jsonl", "JSON Lines (*.jsonl);;All Files (*)"
        )
        if not path:
            return
        try:
            self.export_transcript(path)
        except OSError as exc:
            self._show_error(str(exc))

    def export_transcript(self, path: str) -> None:
        payload = self.application.transcript_jsonl().encode("utf-8")
        output = QSaveFile(path)
        if not output.open(QIODevice.OpenModeFlag.WriteOnly):
            raise OSError(f"could not export transcript: {output.errorString()}")
        if output.write(payload) != len(payload):
            detail = output.errorString()
            output.cancelWriting()
            raise OSError(f"could not export transcript: {detail}")
        if not output.commit():
            raise OSError(f"could not export transcript: {output.errorString()}")

    def poll_serial(self) -> None:
        if self.application.state != ConnectionState.CONNECTED:
            return
        previous_count = len(self.application.messages)
        try:
            for message in self.application.poll():
                self.terminal.append_message(message)
        except HostApplicationError as exc:
            for message in self.application.messages[previous_count:]:
                self.terminal.append_message(message)
            self._show_error(str(exc))
            self._update_state()

    def closeEvent(self, event: QCloseEvent | None) -> None:
        try:
            self.application.disconnect()
        except HostApplicationError as exc:
            self._show_error(str(exc))
            if self.application.backend.is_open:
                self._update_state()
                if event is not None:
                    event.ignore()
                return
        self.poll_timer.stop()
        if event is not None:
            event.accept()

    def _update_state(self) -> None:
        state = self.application.state
        self.connection_panel.set_state(state, self.application.connection.last_error or "")
        self.terminal.set_connected(state == ConnectionState.CONNECTED)

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Host Application", message)

