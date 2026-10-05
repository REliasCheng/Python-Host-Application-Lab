"""Terminal receive view and command input."""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from host_app.models.message import TerminalMessage


class TerminalView(QWidget):
    send_requested = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Received and transmitted lines appear here.")
        self.command = QLineEdit()
        self.command.setPlaceholderText("Enter a line-oriented command")
        self.send_button = QPushButton("Send")
        self.clear_button = QPushButton("Clear")

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.command)
        input_layout.addWidget(self.send_button)
        input_layout.addWidget(self.clear_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.output)
        layout.addLayout(input_layout)

        self.send_button.clicked.connect(self._emit_command)
        self.command.returnPressed.connect(self._emit_command)
        self.clear_button.clicked.connect(self.output.clear)

    def append_message(self, message: TerminalMessage) -> None:
        self.output.appendPlainText(f"[{message.direction.value.upper()}] {message.text}")

    def set_connected(self, connected: bool) -> None:
        self.command.setEnabled(connected)
        self.send_button.setEnabled(connected)

    def _emit_command(self) -> None:
        text = self.command.text().strip()
        if text:
            self.send_requested.emit(text)
            self.command.clear()

