"""Original host application implementation for line-oriented serial devices."""

from host_app.core.application import HostApplication
from host_app.core.config import SerialConfig
from host_app.models.connection import ConnectionState

__all__ = ["ConnectionState", "HostApplication", "SerialConfig"]
__version__ = "0.1.0"

