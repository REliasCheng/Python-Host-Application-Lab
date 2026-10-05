import pytest

from host_app.core.errors import LineTooLongError, ProtocolDecodeError
from host_app.protocol.line_parser import LineParser


def test_parser_accepts_complete_and_split_lines() -> None:
    parser = LineParser()

    assert parser.feed(b"ready\r\npart") == ["ready"]
    assert parser.buffered_bytes == 4
    assert parser.feed(b"ial\nnext\n") == ["partial", "next"]
    assert parser.buffered_bytes == 0


def test_parser_preserves_empty_line() -> None:
    parser = LineParser()

    assert parser.feed(b"\n") == [""]


def test_parser_rejects_invalid_encoding() -> None:
    parser = LineParser(encoding="utf-8")

    with pytest.raises(ProtocolDecodeError):
        parser.feed(b"\xff\n")


def test_parser_accepts_exact_boundary() -> None:
    parser = LineParser(max_line_bytes=4)

    assert parser.feed(b"1234\n") == ["1234"]


def test_parser_drops_overlong_line_and_recovers() -> None:
    parser = LineParser(max_line_bytes=4)

    with pytest.raises(LineTooLongError):
        parser.feed(b"12345")

    assert parser.feed(b"discarded\n") == []
    assert parser.feed(b"ok\n") == ["ok"]


def test_parser_validates_configuration_and_input_type() -> None:
    with pytest.raises(ValueError):
        LineParser(encoding="")
    with pytest.raises(ValueError):
        LineParser(max_line_bytes=0)
    with pytest.raises(ValueError):
        LineParser(encoding="not-a-real-codec")

    parser = LineParser()
    with pytest.raises(TypeError):
        parser.feed("not bytes")  # type: ignore[arg-type]
    parser.feed(b"partial")
    parser.reset()
    assert parser.buffered_bytes == 0

