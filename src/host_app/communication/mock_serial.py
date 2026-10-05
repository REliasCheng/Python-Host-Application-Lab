"""Deterministic in-memory serial backend for host tests and demos."""

from collections import deque

from host_app.communication.interface import SerialBackend
from host_app.core.config import SerialConfig
from host_app.core.errors import CommunicationError, CommunicationTimeout, DisconnectedError
from host_app.models.device import SerialPortInfo


class MockSerialBackend(SerialBackend):
    def __init__(self, *, fail_on_open: str | None = None) -> None:
        self._open = False
        self._fail_on_open = fail_on_open
        self._incoming: deque[bytearray] = deque()
        self._sent: list[bytes] = []
        self._timeout_once = False
        self._disconnect_once = False
        self.last_config: SerialConfig | None = None

    @property
    def is_open(self) -> bool:
        return self._open

    @property
    def sent_data(self) -> tuple[bytes, ...]:
        return tuple(self._sent)

    def available_ports(self) -> list[SerialPortInfo]:
        return [SerialPortInfo("MOCK0", "In-memory serial backend", "MOCK")]

    def open(self, config: SerialConfig) -> None:
        if self._fail_on_open is not None:
            raise CommunicationError(self._fail_on_open)
        self.last_config = config
        self._open = True

    def close(self) -> None:
        self._open = False

    def write(self, payload: bytes) -> int:
        self._require_open()
        if not isinstance(payload, bytes):
            raise TypeError("payload must be bytes")
        self._sent.append(payload)
        return len(payload)

    def read(self, max_bytes: int, timeout: float) -> bytes:
        self._require_open()
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        if timeout < 0:
            raise ValueError("timeout must not be negative")
        if self._disconnect_once:
            self._disconnect_once = False
            self._open = False
            raise DisconnectedError("mock device disconnected")
        if self._timeout_once:
            self._timeout_once = False
            raise CommunicationTimeout("mock read timed out")
        if not self._incoming:
            return b""
        chunk = self._incoming[0]
        result = bytes(chunk[:max_bytes])
        del chunk[:max_bytes]
        if not chunk:
            self._incoming.popleft()
        return result

    def queue_receive(self, payload: bytes) -> None:
        if not isinstance(payload, bytes):
            raise TypeError("payload must be bytes")
        self._incoming.append(bytearray(payload))

    def simulate_timeout(self) -> None:
        self._timeout_once = True

    def simulate_disconnect(self) -> None:
        self._disconnect_once = True

    def _require_open(self) -> None:
        if not self._open:
            raise DisconnectedError("serial backend is not connected")

