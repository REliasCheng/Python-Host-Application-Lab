"""Domain-specific exceptions used across the host application."""


class HostApplicationError(Exception):
    """Base class for expected application errors."""


class InvalidTransitionError(HostApplicationError):
    """Raised when the connection state machine rejects a transition."""


class CommunicationError(HostApplicationError):
    """Raised when a communication backend cannot complete an operation."""


class CommunicationTimeout(CommunicationError):
    """Raised when a communication operation reaches its timeout."""


class DisconnectedError(CommunicationError):
    """Raised when an operation requires an open connection."""


class ProtocolError(HostApplicationError):
    """Base class for line and command protocol errors."""


class ProtocolDecodeError(ProtocolError):
    """Raised when received bytes cannot be decoded."""


class LineTooLongError(ProtocolError):
    """Raised when a line exceeds the configured byte limit."""


class InvalidCommandError(ProtocolError):
    """Raised when an outgoing command is empty or malformed."""

