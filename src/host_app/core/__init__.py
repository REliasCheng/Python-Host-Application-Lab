"""Application coordination, configuration, errors, and connection state."""

from host_app.core.application import HostApplication
from host_app.core.config import SerialConfig
from host_app.core.state import ConnectionStateMachine

__all__ = ["ConnectionStateMachine", "HostApplication", "SerialConfig"]

