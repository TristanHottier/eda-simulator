# core/component.py
from core.pin import Pin


class Component:
    """
    Represents an electronic component in the schematic.
    Stores pins, parameters, and reference designator (ref).
    """

    DEFAULT_PARAMS = {
        "resistor": {"resistance": 1000, "type": "resistor"},
        "capacitor": {"capacitance": 1, "type": "capacitor"},
        "led": {"voltage_drop": 2.0, "type": "led"},
        "generic": {"type": "generic"}
    }

    def __init__(self, ref: str, pins: list[Pin] = None, parameters: dict = None, comp_type: str = "generic"):
        self.ref = ref
        self.pins = pins or []
        self.type = comp_type.lower()  # Store type separately for easier defaults
        # Merge user parameters with default parameters
        default_params = self.DEFAULT_PARAMS.get(self.type, self.DEFAULT_PARAMS["generic"])
        self.parameters = {**default_params, **(parameters or {})}

    def add_pin(self, pin: Pin):
        """Add a new pin to the component"""
        self.pins.append(pin)

    def update_parameter(self, key: str, value):
        """Update a single parameter"""
        self.parameters[key] = value

    def get_parameter(self, key: str, default=None):
        """Return a parameter value"""
        return self.parameters.get(key, default)

    def all_parameters(self):
        """Return all parameter key-value pairs"""
        return self.parameters.items()
