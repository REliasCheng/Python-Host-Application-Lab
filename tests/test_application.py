import pytest

from host_app.communication.mock_serial import MockSerialBackend
from host_app.core.application import HostApplication
from host_app.core.config import SerialConfig
from host_app.core.errors import (
    CommunicationError,
    DisconnectedError,
    ProtocolDecodeError,
)
from host_app.models.connection import ConnectionState
from host_app.models.message import MessageDirection


def test_application_connect_send_receive_disconnect() -> None:
    backend = MockSerialBackend()
    app = HostApplication(backend)

    assert app.available_ports()[0].port == "MOCK0"
    app.connect(SerialConfig("MOCK0", max_line_bytes=32))
    assert app.state == ConnectionState.CONNECTED

    tx = app.send_command("set mode 2")
    assert tx.direction == MessageDirection.TX
    assert backend.sent_data == (b"set mode 2\r\n",)

    backend.queue_receive(b"ready\nvalue=2\r\n")
    messages = app.poll()
    assert [item.text for item in messages] == ["ready", "value=2"]
    assert all(item.direction == MessageDirection.RX for item in messages)
    assert len(app.messages) == 3

    app.disconnect()
    assert app.state == ConnectionState.DISCONNECTED
    assert not backend.is_open


def test_timeout_is_nonfatal() -> None:
    backend = MockSerialBackend()
    app = HostApplication(backend)
    app.connect(SerialConfig("MOCK0"))
    backend.simulate_timeout()

    assert app.poll() == []
    assert app.state == ConnectionState.CONNECTED


def test_open_and_disconnect_failures_propagate_to_error_state() -> None:
    backend = MockSerialBackend(fail_on_open="permission denied")
    app = HostApplication(backend)

    with pytest.raises(CommunicationError):
        app.connect(SerialConfig("MOCK0"))
    assert app.state == ConnectionState.ERROR
    assert app.connection.last_error == "permission denied"

    app.disconnect()
    assert app.state == ConnectionState.DISCONNECTED


def test_runtime_disconnect_enters_error_state() -> None:
    backend = MockSerialBackend()
    app = HostApplication(backend)
    app.connect(SerialConfig("MOCK0"))
    backend.simulate_disconnect()

    with pytest.raises(DisconnectedError):
        app.poll()
    assert app.state == ConnectionState.ERROR


def test_decode_failure_enters_error_state() -> None:
    backend = MockSerialBackend()
    app = HostApplication(backend)
    app.connect(SerialConfig("MOCK0", encoding="utf-8"))
    backend.queue_receive(b"\xff\n")

    with pytest.raises(ProtocolDecodeError):
        app.poll()
    assert app.state == ConnectionState.ERROR


def test_application_reconnects_after_runtime_disconnect() -> None:
    backend = MockSerialBackend()
    app = HostApplication(backend)
    config = SerialConfig("MOCK0")
    app.connect(config)
    backend.queue_receive(b"stale-partial")
    assert app.poll() == []

    backend.simulate_disconnect()
    with pytest.raises(DisconnectedError):
        app.poll()
    assert app.state == ConnectionState.ERROR

    app.connect(config)
    backend.queue_receive(b"fresh\n")
    assert [message.text for message in app.poll()] == ["fresh"]
    assert app.state == ConnectionState.CONNECTED


def test_connected_operations_are_guarded() -> None:
    app = HostApplication(MockSerialBackend())

    with pytest.raises(DisconnectedError):
        app.send_command("status")
    with pytest.raises(DisconnectedError):
        app.poll()


def test_close_failure_is_recoverable() -> None:
    class CloseFailsOnce(MockSerialBackend):
        failures = 1

        def close(self) -> None:
            super().close()
            if self.failures:
                self.failures -= 1
                raise CommunicationError("device vanished during close")

    backend = CloseFailsOnce()
    app = HostApplication(backend)
    app.connect(SerialConfig("MOCK0"))
    with pytest.raises(CommunicationError, match="vanished"):
        app.disconnect()
    assert app.state == ConnectionState.DISCONNECTED
    app.connect(SerialConfig("MOCK0"))
    assert app.state == ConnectionState.CONNECTED
    app.disconnect()


@pytest.mark.parametrize(
    "changes",
    [
        {"port": ""},
        {"port": "MOCK0", "baudrate": 0},
        {"port": "MOCK0", "encoding": ""},
        {"port": "MOCK0", "encoding": "not-a-real-codec"},
        {"port": "MOCK0", "line_ending": "x"},
        {"port": "MOCK0", "read_size": 0},
        {"port": "MOCK0", "read_timeout": -1},
        {"port": "MOCK0", "max_line_bytes": 0},
    ],
)
def test_serial_config_validation(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        SerialConfig(**changes)  # type: ignore[arg-type]

