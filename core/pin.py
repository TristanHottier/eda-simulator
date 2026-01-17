# core/pin.py
from enum import Enum, auto
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.net import Net


class PinDirection(Enum):
    """Defines the electrical nature of a component pin."""
    INPUT = auto()
    OUTPUT = auto()
    BIDIRECTIONAL = auto()


class Pin:
    """
    Represents a physical/logical connection point on a component.
    """

    def __init__(self, name: str, direction: PinDirection, rel_x: float = 0, rel_y: float = 0):
        self.name: str = name
        self.direction: PinDirection = direction
        self.net: Optional['Net'] = None

        # FIX: Store relative coordinates for UI placement
        self.rel_x = rel_x
        self.rel_y = rel_y