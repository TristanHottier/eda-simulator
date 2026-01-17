# core/net.py
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from core.pin import Pin


class Net:
    """
    Represents a logical electrical connection (wire) between multiple pins.
    """
    def __init__(self, name: str):
        self.name = name
        self.pins: List['Pin'] = []

    def connect(self, pin: 'Pin') -> None:
        """
        Connects a pin to this net and updates the pin's net reference.
        """
        self.pins.append(pin)
        pin.net = self