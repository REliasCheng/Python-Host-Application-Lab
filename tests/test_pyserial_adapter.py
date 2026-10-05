from types import SimpleNamespace

import pytest

from host_app.communication.pyserial_adapter import PySerialBackend
from host_app.core.config import SerialConfig
from host_app.core.errors import (
    CommunicationError,
    CommunicationTimeout,
    DisconnectedError,
)


class FakeSerialException(Exception):
    pass


class FakeSerialTimeoutException(FakeSerialException):
    pass


class FakeConnection:
    def __init__(self) -> None:
        self.is_open = True
        self.timeout = 0.0
        self.written: list[bytes] = []
        self.incoming = b"ready\n"
        self.write_error: Exception | None = None
        self.read_error: Exception | None = None

    def close(self) -> None:
        self.is_open = False

    def write(self, payload: bytes) -> int:
        if self.write_error is not None:
            raise self.write_error
        self.written.append(payload)
        return len(payload)

    def read(self, max_bytes: int) -> bytes:
        if self.read_error is not None:
            raise self.read_error
        return self.incoming[:max_bytes]


def install_fake_modules(
    monkeypatch: pytest.MonkeyPatch,
    *,
    open_error: Exception | None = None,
) -> tuple[FakeConnection, dict[str, object]]:
    connection = FakeConnection()
    captured: dict[str, object] = {}

    def create_serial(**kwargs: object) -> FakeConnection:
        if open_error is not None:
            raise open_error
        captured.update(kwargs)
        return connection

    serial_module = SimpleNamespace(
        Serial=create_serial,
        SerialException=FakeSerialException,
        SerialTimeoutException=FakeSerialTimeoutException,
    )
    list_ports = SimpleNamespace(
        comports=lambda: [
            SimpleNamespace(device="COM7", description="Test port", hwid="FAKE")
        ]
    )
    monkeypatch.setattr(
        PySerialBackend,
        "_modules",
        staticmethod(lambda: (serial_module, list_ports)),
    )
    return connection, captured


def test_pyserial_adapter_open_read_write_close(monkeypatch: pytest.MonkeyPatch) -> None:
    connection, captured = install_fake_modules(monkeypatch)
    backend = PySerialBackend()

    assert backend.available_ports()[0].port == "COM7"
    backend.open(SerialConfig("COM7", baudrate=57_600, read_timeout=0.2))
    assert backend.is_open
    assert captured == {
        "port": "COM7",
        "baudrate": 57_600,
        "timeout": 0.2,
        "write_timeout": 0.2,
    }
    assert backend.write(b"status\r\n") == 8
    assert connection.written == [b"status\r\n"]
    assert backend.read(4, 0.1) == b"read"
    assert connection.timeout == 0.1

    backend.close()
    assert not backend.is_open


def test_pyserial_adapter_maps_open_and_io_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    install_fake_modules(monkeypatch, open_error=FakeSerialException("busy"))
    backend = PySerialBackend()
    with pytest.raises(CommunicationError, match="could not open"):
        backend.open(SerialConfig("COM7"))

    connection, _ = install_fake_modules(monkeypatch)
    backend.open(SerialConfig("COM7"))
    connection.write_error = FakeSerialTimeoutException("timeout")
    with pytest.raises(CommunicationTimeout):
        backend.write(b"status\r\n")

    connection.write_error = None
    connection.read_error = FakeSerialException("disconnected")
    with pytest.raises(CommunicationError, match="serial read failed"):
        backend.read(8, 0.1)


def test_pyserial_adapter_validates_disconnected_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_modules(monkeypatch)
    backend = PySerialBackend()

    with pytest.raises(DisconnectedError):
        backend.write(b"status\r\n")
    with pytest.raises(DisconnectedError):
        backend.read(8, 0.1)
