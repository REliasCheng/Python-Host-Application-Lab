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


def test_parser_accepts_exact_boundary_with_crlf_across_chunks() -> None:
    parser = LineParser(max_line_bytes=4)

    assert parser.feed(b"1234\r") == []
    assert parser.feed(b"\n") == ["1234"]


def test_parser_rejects_overlong_crlf_and_recovers() -> None:
    parser = LineParser(max_line_bytes=4)

    with pytest.raises(LineTooLongError):
        parser.feed(b"12345\r\n")
    assert parser.feed(b"ok\r\n") == ["ok"]


def test_parser_rejects_cr_that_is_not_followed_by_lf_at_boundary() -> None:
    parser = LineParser(max_line_bytes=4)

    assert parser.feed(b"1234\r") == []
    with pytest.raises(LineTooLongError):
        parser.feed(b"x\n")
    assert parser.feed(b"ok\n") == ["ok"]


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


@pytest.mark.parametrize(
    ("chunk", "error_type", "completed"),
    [
        (b"12345\nok\n", LineTooLongError, ["ok"]),
        (b"ok\n12345\n", LineTooLongError, ["ok"]),
        (b"ok\n\xff\n", ProtocolDecodeError, ["ok"]),
        (b"\xff\nok\n", ProtocolDecodeError, ["ok"]),
        (b"12345\n\xff\nok\n67890\n", LineTooLongError, ["ok"]),
    ],
)
def test_errors_consume_entire_chunk_and_deliver_completed_lines(
    chunk: bytes, error_type: type[Exception], completed: list[str]
) -> None:
    parser = LineParser(max_line_bytes=4)
    with pytest.raises(error_type) as caught:
        parser.feed(chunk)
    assert caught.value.completed_lines == completed
    assert parser.feed(b"next\n") == ["next"]


def test_split_utf8_empty_crlf_and_multiple_error_metadata() -> None:
    parser = LineParser(max_line_bytes=4)
    assert parser.feed(b"\xc3") == []
    assert parser.feed(b"\xa9\n\r\n") == ["é", ""]
    with pytest.raises(LineTooLongError) as caught:
        parser.feed(b"12345\n\xff\n45678\ngood\n")
    assert caught.value.completed_lines == ["good"]
    assert len(caught.value.frame_errors) == 3
    assert isinstance(caught.value.frame_errors[1], ProtocolDecodeError)
    assert parser.feed(b"ok\n") == ["ok"]


def test_overlong_frame_split_across_chunks_discards_through_lf() -> None:
    parser = LineParser(max_line_bytes=4)
    assert parser.feed(b"1234") == []
    with pytest.raises(LineTooLongError):
        parser.feed(b"5abc")
    assert parser.feed(b"more\nOK\n") == ["OK"]

