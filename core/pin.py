# core/pin.py
from enum import Enum, auto


class PinDirection(Enum):
    INPUT = auto()
    OUTPUT = auto()
    BIDIRECTIONAL = auto()


class Pin:
    def __init__(self, name: str, direction: PinDirection):
        self.name = name
        self.direction = direction
        self.net = None  # type: Net | None
