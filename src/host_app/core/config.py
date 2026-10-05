"""Validated configuration models for serial communication."""

import codecs
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SerialConfig:
    """Runtime configuration passed to a serial backend."""

    port: str
    baudrate: int = 115_200
    encoding: str = "utf-8"
    line_ending: str = "\r\n"
    read_size: int = 256
    read_timeout: float = 0.05
    max_line_bytes: int = 256

    def __post_init__(self) -> None:
        if not self.port.strip():
            raise ValueError("port must not be empty")
        if self.baudrate <= 0:
            raise ValueError("baudrate must be positive")
        if not self.encoding.strip():
            raise ValueError("encoding must not be empty")
        try:
            codecs.lookup(self.encoding)
        except LookupError as exc:
            raise ValueError(f"unknown encoding: {self.encoding}") from exc
        if self.line_ending not in {"\n", "\r\n"}:
            raise ValueError("line_ending must be LF or CRLF")
        if self.read_size <= 0:
            raise ValueError("read_size must be positive")
        if self.read_timeout < 0:
            raise ValueError("read_timeout must not be negative")
        if self.max_line_bytes <= 0:
            raise ValueError("max_line_bytes must be positive")

