import pytest

from host_app.core.errors import InvalidCommandError
from host_app.protocol.command import encode_command, parse_command


def test_parse_command_supports_arguments_and_quotes() -> None:
    parsed = parse_command('set label "motor one"')

    assert parsed.name == "set"
    assert parsed.arguments == ("label", "motor one")


@pytest.mark.parametrize("text", ["", "   ", "1status", "bad/name"])
def test_parse_command_rejects_invalid_input(text: str) -> None:
    with pytest.raises(InvalidCommandError):
        parse_command(text)


def test_parse_command_rejects_unclosed_quote_and_token_overflow() -> None:
    with pytest.raises(InvalidCommandError):
        parse_command('set "unterminated')
    with pytest.raises(InvalidCommandError):
        parse_command("cmd a b", max_tokens=2)
    with pytest.raises(ValueError):
        parse_command("cmd", max_tokens=0)
    with pytest.raises(TypeError):
        parse_command(1)  # type: ignore[arg-type]


def test_encode_command_normalizes_and_appends_terminator() -> None:
    assert encode_command('  set mode "safe"  ') == b"set mode safe\r\n"


def test_encode_command_rejects_line_break_encoding_and_size_errors() -> None:
    with pytest.raises(InvalidCommandError):
        encode_command("status\nreset")
    with pytest.raises(InvalidCommandError):
        encode_command("status", max_payload_bytes=3)
    with pytest.raises(InvalidCommandError):
        encode_command("send \u6d4b\u8bd5", encoding="ascii")
    with pytest.raises(ValueError):
        encode_command("status", encoding="not-a-real-codec")
    with pytest.raises(ValueError):
        encode_command("status", line_ending="")
    with pytest.raises(ValueError):
        encode_command("status", max_payload_bytes=0)

