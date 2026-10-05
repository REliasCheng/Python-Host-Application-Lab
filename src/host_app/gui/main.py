"""GUI entry point installed as the ``host-app`` command."""

import sys

from PyQt5.QtWidgets import QApplication

from host_app.gui.main_window import MainWindow


def main() -> int:
    application = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return int(application.exec_())


if __name__ == "__main__":  # pragma: no cover - manual entry point
    raise SystemExit(main())

