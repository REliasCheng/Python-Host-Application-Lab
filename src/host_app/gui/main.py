"""GUI entry point installed as the ``host-app`` command."""

import argparse
import sys

from PyQt5.QtWidgets import QApplication

from host_app.communication.mock_serial import MockSerialBackend
from host_app.gui.main_window import MainWindow


class DemoMockSerialBackend(MockSerialBackend):
    """Give the visible mock GUI a labeled deterministic response."""

    def write(self, payload: bytes) -> int:
        written = super().write(payload)
        self.queue_receive(b"MOCK ACK: " + payload.rstrip(b"\r\n") + b"\n")
        return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Python serial host application")
    parser.add_argument("--mock", action="store_true", help="run GUI with in-memory MOCK0 (no hardware)")
    args = parser.parse_args(argv)
    application = QApplication([sys.argv[0]])
    window = MainWindow(DemoMockSerialBackend() if args.mock else None)
    if args.mock:
        window.setWindowTitle("Python Host Application Lab — MOCK0 demo (no device)")
    window.show()
    return int(application.exec_())


if __name__ == "__main__":  # pragma: no cover - manual entry point
    raise SystemExit(main())

