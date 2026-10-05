"""Terminal message models kept independent of GUI widgets."""

from dataclasses import dataclass
from enum import Enum


class MessageDirection(str, Enum):
    TX = "tx"
    RX = "rx"


@dataclass(frozen=True, slots=True)
class TerminalMessage:
    direction: MessageDirection
    text: str

