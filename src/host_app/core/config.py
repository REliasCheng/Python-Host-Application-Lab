"""Validated configuration models for serial communication."""

import codecs
import math
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
        for name in ("baudrate", "read_size", "max_line_bytes"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if not self.encoding.strip():
            raise ValueError("encoding must not be empty")
        try:
            codecs.lookup(self.encoding)
        except LookupError as exc:
            raise ValueError(f"unknown encoding: {self.encoding}") from exc
        if self.line_ending not in {"\n", "\r\n"}:
            raise ValueError("line_ending must be LF or CRLF")
        timeout = self.read_timeout
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or (isinstance(timeout, float) and not math.isfinite(timeout))
            or timeout < 0
        ):
            raise ValueError("read_timeout must be finite and nonnegative")

