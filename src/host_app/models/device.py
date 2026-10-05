"""Serial device discovery models."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SerialPortInfo:
    port: str
    description: str = ""
    hardware_id: str = ""

    @property
    def display_name(self) -> str:
        return f"{self.port} — {self.description}" if self.description else self.port

