"""Port selection and connection controls."""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QWidget

from host_app.models.connection import ConnectionState
from host_app.models.device import SerialPortInfo


class ConnectionPanel(QWidget):
    connect_requested = pyqtSignal(str, int)
    disconnect_requested = pyqtSignal()
    refresh_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        self.port_combo.setMinimumWidth(220)
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("115200")
        self.refresh_button = QPushButton("Refresh")
        self.connect_button = QPushButton("Connect")
        self.status_label = QLabel("Disconnected")

        layout = QHBoxLayout(self)
        layout.addWidget(QLabel("Port"))
        layout.addWidget(self.port_combo)
        layout.addWidget(QLabel("Baud"))
        layout.addWidget(self.baud_combo)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.connect_button)
        layout.addWidget(self.status_label)

        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        self.connect_button.clicked.connect(self._on_connect_clicked)
        self._state = ConnectionState.DISCONNECTED
        self.set_state(self._state)

    def set_ports(self, ports: list[SerialPortInfo]) -> None:
        current = self.port_combo.currentText().strip()
        self.port_combo.clear()
        for port in ports:
            self.port_combo.addItem(port.display_name, port.port)
        if current and self.port_combo.findData(current) < 0:
            self.port_combo.addItem(current, current)

    def set_state(self, state: ConnectionState, detail: str = "") -> None:
        self._state = state
        labels = {
            ConnectionState.DISCONNECTED: ("Disconnected", "#475569"),
            ConnectionState.CONNECTING: ("Connecting", "#b45309"),
            ConnectionState.CONNECTED: ("Connected", "#15803d"),
            ConnectionState.ERROR: ("Error", "#b91c1c"),
        }
        text, color = labels[state]
        if detail:
            text = f"{text}: {detail}"
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"font-weight: 600; color: {color};")
        self.connect_button.setText("Disconnect" if state == ConnectionState.CONNECTED else "Connect")
        self.connect_button.setEnabled(state != ConnectionState.CONNECTING)
        controls_enabled = state not in {ConnectionState.CONNECTED, ConnectionState.CONNECTING}
        self.port_combo.setEnabled(controls_enabled)
        self.baud_combo.setEnabled(controls_enabled)
        self.refresh_button.setEnabled(controls_enabled)

    def _on_connect_clicked(self) -> None:
        if self._state == ConnectionState.CONNECTED:
            self.disconnect_requested.emit()
            return
        port = self.port_combo.currentData() or self.port_combo.currentText().strip()
        try:
            baudrate = int(self.baud_combo.currentText())
        except ValueError:
            baudrate = 0
        self.connect_requested.emit(str(port), baudrate)

