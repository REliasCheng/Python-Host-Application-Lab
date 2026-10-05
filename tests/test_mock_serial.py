import pytest

from host_app.communication.mock_serial import MockSerialBackend
from host_app.core.config import SerialConfig
from host_app.core.errors import (
    CommunicationError,
    CommunicationTimeout,
    DisconnectedError,
)


def test_mock_backend_connect_send_receive_and_close() -> None:
    backend = MockSerialBackend()
    config = SerialConfig("MOCK0")

    assert backend.available_ports()[0].display_name.startswith("MOCK0")
    backend.open(config)
    assert backend.is_open
    assert backend.last_config == config
    assert backend.write(b"status\r\n") == 8
    assert backend.sent_data == (b"status\r\n",)

    backend.queue_receive(b"one\ntwo\n")
    assert backend.read(4, 0) == b"one\n"
    assert backend.read(32, 0) == b"two\n"
    assert backend.read(32, 0) == b""

    backend.close()
    assert not backend.is_open
    with pytest.raises(DisconnectedError):
        backend.write(b"x")


def test_mock_backend_timeout_and_disconnect_simulation() -> None:
    backend = MockSerialBackend()
    backend.open(SerialConfig("MOCK0"))
    backend.simulate_timeout()
    with pytest.raises(CommunicationTimeout):
        backend.read(1, 0.1)

    backend.simulate_disconnect()
    with pytest.raises(DisconnectedError):
        backend.read(1, 0.1)
    assert not backend.is_open


def test_mock_backend_validates_operations() -> None:
    backend = MockSerialBackend(fail_on_open="open failed")
    with pytest.raises(CommunicationError):
        backend.open(SerialConfig("MOCK0"))

    backend = MockSerialBackend()
    backend.open(SerialConfig("MOCK0"))
    with pytest.raises(TypeError):
        backend.write("text")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        backend.queue_receive("text")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        backend.read(0, 0)
    with pytest.raises(ValueError):
        backend.read(1, -1)

