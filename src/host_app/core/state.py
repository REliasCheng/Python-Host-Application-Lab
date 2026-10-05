"""Connection-state validation independent of GUI and serial libraries."""

from host_app.core.errors import InvalidTransitionError
from host_app.models.connection import ConnectionState

_ALLOWED_TRANSITIONS: dict[ConnectionState, frozenset[ConnectionState]] = {
    ConnectionState.DISCONNECTED: frozenset({ConnectionState.CONNECTING}),
    ConnectionState.CONNECTING: frozenset(
        {ConnectionState.CONNECTED, ConnectionState.DISCONNECTED, ConnectionState.ERROR}
    ),
    ConnectionState.CONNECTED: frozenset({ConnectionState.DISCONNECTED, ConnectionState.ERROR}),
    ConnectionState.ERROR: frozenset({ConnectionState.DISCONNECTED, ConnectionState.CONNECTING}),
}


class ConnectionStateMachine:
    """Small explicit state machine for connection lifecycle changes."""

    def __init__(self) -> None:
        self._state = ConnectionState.DISCONNECTED
        self._last_error: str | None = None

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def transition(self, target: ConnectionState) -> ConnectionState:
        if target == self._state:
            return self._state
        if target not in _ALLOWED_TRANSITIONS[self._state]:
            raise InvalidTransitionError(
                f"invalid connection transition: {self._state.value} -> {target.value}"
            )
        self._state = target
        if target != ConnectionState.ERROR:
            self._last_error = None
        return self._state

    def fail(self, error: Exception | str) -> ConnectionState:
        message = str(error).strip() or error.__class__.__name__
        if self._state == ConnectionState.DISCONNECTED:
            raise InvalidTransitionError("cannot enter error state while disconnected")
        self.transition(ConnectionState.ERROR)
        self._last_error = message
        return self._state

    def disconnect(self) -> ConnectionState:
        if self._state == ConnectionState.DISCONNECTED:
            return self._state
        return self.transition(ConnectionState.DISCONNECTED)

