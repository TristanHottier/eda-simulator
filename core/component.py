# core/component.py
from core.pin import Pin


class Component:
    def __init__(self, ref: str, pins: list[Pin], parameters: dict = None):
        self.ref = ref
        self.pins = pins
        self.parameters = parameters or {}
