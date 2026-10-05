"""Incremental line parser with explicit size and decoding boundaries."""

import codecs

from host_app.core.errors import LineTooLongError, ProtocolDecodeError


class LineParser:
    def __init__(self, *, encoding: str = "utf-8", max_line_bytes: int = 256) -> None:
        if not encoding.strip():
            raise ValueError("encoding must not be empty")
        try:
            codecs.lookup(encoding)
        except LookupError as exc:
            raise ValueError(f"unknown encoding: {encoding}") from exc
        if max_line_bytes <= 0:
            raise ValueError("max_line_bytes must be positive")
        self.encoding = encoding
        self.max_line_bytes = max_line_bytes
        self._buffer = bytearray()
        self._discarding = False

    @property
    def buffered_bytes(self) -> int:
        return len(self._buffer)

    def reset(self) -> None:
        self._buffer.clear()
        self._discarding = False

    def feed(self, data: bytes) -> list[str]:
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        lines: list[str] = []
        for value in data:
            if self._discarding:
                if value == 0x0A:
                    self._discarding = False
                continue
            if value == 0x0A:
                payload = bytes(self._buffer)
                self._buffer.clear()
                if payload.endswith(b"\r"):
                    payload = payload[:-1]
                try:
                    lines.append(payload.decode(self.encoding, errors="strict"))
                except UnicodeDecodeError as exc:
                    raise ProtocolDecodeError(
                        f"received line is not valid {self.encoding}"
                    ) from exc
                continue
            if len(self._buffer) >= self.max_line_bytes:
                self._buffer.clear()
                self._discarding = True
                raise LineTooLongError(
                    f"received line exceeds {self.max_line_bytes} bytes"
                )
            self._buffer.append(value)
        return lines

