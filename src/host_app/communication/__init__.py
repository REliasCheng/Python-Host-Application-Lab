"""Serial backends with hardware-independent interfaces."""

from host_app.communication.interface import SerialBackend
from host_app.communication.mock_serial import MockSerialBackend
from host_app.communication.pyserial_adapter import PySerialBackend

__all__ = ["MockSerialBackend", "PySerialBackend", "SerialBackend"]

