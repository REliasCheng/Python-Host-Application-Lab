"""Optional pyserial adapter; pyserial itself is never vendored."""

from typing import Any

from host_app.communication.interface import SerialBackend
from host_app.core.config import SerialConfig
from host_app.core.errors import (
    CommunicationError,
    CommunicationTimeout,
    DisconnectedError,
)
from host_app.models.device import SerialPortInfo


class PySerialBackend(SerialBackend):
    def __init__(self) -> None:
        self._serial: Any | None = None

    @property
    def is_open(self) -> bool:
        return bool(self._serial is not None and self._serial.is_open)

    @staticmethod
    def _modules() -> tuple[Any, Any]:
        try:
            import serial
            from serial.tools import list_ports
        except ImportError as exc:
            raise CommunicationError(
                "pyserial is required; install the 'serial' optional dependency"
            ) from exc
        return serial, list_ports

    def available_ports(self) -> list[SerialPortInfo]:
        serial, list_ports = self._modules()
        try:
            return [
                SerialPortInfo(item.device, item.description or "", item.hwid or "")
                for item in list_ports.comports()
            ]
        except (serial.SerialException, OSError) as exc:
            raise CommunicationError(f"could not list serial ports: {exc}") from exc

    def open(self, config: SerialConfig) -> None:
        serial, _ = self._modules()
        self.close()
        try:
            self._serial = serial.Serial(
                port=config.port,
                baudrate=config.baudrate,
                timeout=config.read_timeout,
                write_timeout=config.read_timeout,
            )
        except (serial.SerialException, OSError, ValueError) as exc:
            self._serial = None
            raise CommunicationError(f"could not open {config.port}: {exc}") from exc

    def close(self) -> None:
        connection = self._serial
        if connection is not None:
            try:
                connection.close()
            except Exception as exc:
                raise CommunicationError(f"serial close failed: {exc}") from exc
            finally:
                self._serial = None

    def write(self, payload: bytes) -> int:
        serial, _ = self._modules()
        connection = self._serial
        if connection is None or not connection.is_open:
            raise DisconnectedError("serial port is not connected")
        try:
            return int(connection.write(payload))
        except serial.SerialTimeoutException as exc:
            raise CommunicationTimeout("serial write timed out") from exc
        except (serial.SerialException, OSError) as exc:
            raise CommunicationError(f"serial write failed: {exc}") from exc

    def read(self, max_bytes: int, timeout: float) -> bytes:
        serial, _ = self._modules()
        connection = self._serial
        if connection is None or not connection.is_open:
            raise DisconnectedError("serial port is not connected")
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        if timeout < 0:
            raise ValueError("timeout must not be negative")
        try:
            connection.timeout = timeout
            return bytes(connection.read(max_bytes))
        except (serial.SerialException, OSError) as exc:
            raise CommunicationError(f"serial read failed: {exc}") from exc

