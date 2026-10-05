"""Validation and encoding for outgoing line-oriented commands."""

import codecs
import re
import shlex
from dataclasses import dataclass

from host_app.core.errors import InvalidCommandError

_COMMAND_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


@dataclass(frozen=True, slots=True)
class ParsedCommand:
    name: str
    arguments: tuple[str, ...]


def parse_command(text: str, *, max_tokens: int = 16) -> ParsedCommand:
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    try:
        tokens = shlex.split(text.strip())
    except ValueError as exc:
        raise InvalidCommandError(str(exc)) from exc
    if not tokens:
        raise InvalidCommandError("command must not be empty")
    if len(tokens) > max_tokens:
        raise InvalidCommandError(f"command exceeds {max_tokens} tokens")
    if _COMMAND_NAME.fullmatch(tokens[0]) is None:
        raise InvalidCommandError("command name must start with a letter")
    return ParsedCommand(tokens[0], tuple(tokens[1:]))


def encode_command(
    text: str,
    *,
    encoding: str = "utf-8",
    line_ending: str = "\r\n",
    max_payload_bytes: int = 256,
) -> bytes:
    if line_ending not in {"\n", "\r\n"}:
        raise ValueError("line_ending must be LF or CRLF")
    if max_payload_bytes <= 0:
        raise ValueError("max_payload_bytes must be positive")
    try:
        codecs.lookup(encoding)
    except LookupError as exc:
        raise ValueError(f"unknown encoding: {encoding}") from exc
    if "\r" in text or "\n" in text:
        raise InvalidCommandError("command must not contain line breaks")
    parsed = parse_command(text)
    normalized = " ".join((parsed.name, *parsed.arguments))
    try:
        payload = f"{normalized}{line_ending}".encode(encoding, errors="strict")
    except UnicodeEncodeError as exc:
        raise InvalidCommandError(f"command is not valid {encoding}") from exc
    if len(payload) > max_payload_bytes:
        raise InvalidCommandError(f"encoded command exceeds {max_payload_bytes} bytes")
    return payload

