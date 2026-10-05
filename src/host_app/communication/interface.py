"""Backend contract used by the application core."""

from abc import ABC, abstractmethod

from host_app.core.config import SerialConfig
from host_app.models.device import SerialPortInfo


class SerialBackend(ABC):
    @property
    @abstractmethod
    def is_open(self) -> bool:
        """Return whether the backend currently owns an open connection."""

    @abstractmethod
    def available_ports(self) -> list[SerialPortInfo]:
        """Return ports visible to this backend."""

    @abstractmethod
    def open(self, config: SerialConfig) -> None:
        """Open the selected serial endpoint."""

    @abstractmethod
    def close(self) -> None:
        """Close the endpoint. Implementations should be idempotent."""

    @abstractmethod
    def write(self, payload: bytes) -> int:
        """Write bytes or raise a communication exception."""

    @abstractmethod
    def read(self, max_bytes: int, timeout: float) -> bytes:
        """Read up to max_bytes, returning empty bytes when no data is ready."""

