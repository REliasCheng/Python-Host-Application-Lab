"""Hardware-independent application coordinator."""

from host_app.communication.interface import SerialBackend
from host_app.core.config import SerialConfig
from host_app.core.errors import CommunicationError, CommunicationTimeout, DisconnectedError, ProtocolError
from host_app.core.state import ConnectionStateMachine
from host_app.models.connection import ConnectionState
from host_app.models.device import SerialPortInfo
from host_app.models.message import MessageDirection, TerminalMessage
from host_app.protocol.command import encode_command
from host_app.protocol.line_parser import LineParser


class HostApplication:
    """Coordinates state, framing, and a pluggable serial backend."""

    def __init__(self, backend: SerialBackend) -> None:
        self.backend = backend
        self.connection = ConnectionStateMachine()
        self.config: SerialConfig | None = None
        self.messages: list[TerminalMessage] = []
        self._parser = LineParser()

    @property
    def state(self) -> ConnectionState:
        return self.connection.state

    def available_ports(self) -> list[SerialPortInfo]:
        return self.backend.available_ports()

    def connect(self, config: SerialConfig) -> None:
        self.connection.transition(ConnectionState.CONNECTING)
        self.config = config
        self._parser = LineParser(
            encoding=config.encoding,
            max_line_bytes=config.max_line_bytes,
        )
        try:
            self.backend.open(config)
            if not self.backend.is_open:
                raise CommunicationError("backend did not enter the open state")
        except CommunicationError as exc:
            self.connection.fail(exc)
            raise
        self.connection.transition(ConnectionState.CONNECTED)

    def disconnect(self) -> None:
        try:
            self.backend.close()
        finally:
            self._parser.reset()
            self.connection.disconnect()

    def send_command(self, command: str) -> TerminalMessage:
        config = self._connected_config()
        payload = encode_command(
            command,
            encoding=config.encoding,
            line_ending=config.line_ending,
            max_payload_bytes=config.max_line_bytes,
        )
        try:
            written = self.backend.write(payload)
        except CommunicationError as exc:
            self.connection.fail(exc)
            raise
        if written != len(payload):
            error = CommunicationError(
                f"partial serial write: expected {len(payload)} bytes, wrote {written}"
            )
            self.connection.fail(error)
            raise error
        message = TerminalMessage(MessageDirection.TX, command.strip())
        self.messages.append(message)
        return message

    def poll(self) -> list[TerminalMessage]:
        config = self._connected_config()
        try:
            payload = self.backend.read(config.read_size, config.read_timeout)
        except CommunicationTimeout:
            return []
        except CommunicationError as exc:
            self.connection.fail(exc)
            raise
        if not payload:
            return []
        try:
            lines = self._parser.feed(payload)
        except ProtocolError as exc:
            self.connection.fail(exc)
            raise
        messages = [TerminalMessage(MessageDirection.RX, line) for line in lines]
        self.messages.extend(messages)
        return messages

    def _connected_config(self) -> SerialConfig:
        if self.state != ConnectionState.CONNECTED or self.config is None:
            raise DisconnectedError("operation requires a connected backend")
        return self.config

