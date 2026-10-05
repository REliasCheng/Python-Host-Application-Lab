import pytest

from host_app.core.errors import InvalidTransitionError
from host_app.core.state import ConnectionStateMachine
from host_app.models.connection import ConnectionState


def test_valid_connection_lifecycle() -> None:
    state = ConnectionStateMachine()

    assert state.transition(ConnectionState.CONNECTING) == ConnectionState.CONNECTING
    assert state.transition(ConnectionState.CONNECTED) == ConnectionState.CONNECTED
    assert state.disconnect() == ConnectionState.DISCONNECTED
    assert state.disconnect() == ConnectionState.DISCONNECTED


def test_invalid_transition_is_rejected() -> None:
    state = ConnectionStateMachine()

    with pytest.raises(InvalidTransitionError):
        state.transition(ConnectionState.CONNECTED)

    state.transition(ConnectionState.CONNECTING)
    state.transition(ConnectionState.CONNECTED)
    with pytest.raises(InvalidTransitionError):
        state.transition(ConnectionState.CONNECTING)

    state.transition(ConnectionState.ERROR)
    with pytest.raises(InvalidTransitionError):
        state.transition(ConnectionState.CONNECTED)


def test_error_is_recorded_and_can_reconnect() -> None:
    state = ConnectionStateMachine()
    state.transition(ConnectionState.CONNECTING)

    assert state.fail("port unavailable") == ConnectionState.ERROR
    assert state.last_error == "port unavailable"
    assert state.transition(ConnectionState.CONNECTING) == ConnectionState.CONNECTING
    assert state.last_error is None


def test_disconnected_state_cannot_fail() -> None:
    state = ConnectionStateMachine()

    with pytest.raises(InvalidTransitionError):
        state.fail(RuntimeError())

