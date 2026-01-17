# core/component.py
from typing import List, Dict, Any, Optional
from core.pin import Pin, PinDirection


class Component:
    """
    Represents an electronic component in the schematic.
    Stores pins, parameters, and reference designator (ref).
    """

    DEFAULT_PARAMS = {
        "resistor": {"resistance": 1000, "type": "resistor"},
        "capacitor": {"capacitance": 1, "type": "capacitor"},
        "led": {"voltage_drop": 2.0, "type": "led"},
        "inductor" : {"inductance": 100, "type": "inductor"},
        "generic": {"type": "generic"}
    }

    def __init__(self, ref: str, pins: Optional[List[Pin]] = None,
                 parameters: Optional[Dict[str, Any]] = None, comp_type: str = "generic"):
        self.ref = ref
        self.type = comp_type.lower()

        # Merge default parameters
        base_params = self.DEFAULT_PARAMS.get(self.type, self.DEFAULT_PARAMS["generic"])
        self.parameters = {**base_params, **(parameters or {})}

        # FIX: Automatically generate entry and exit pins if none are provided
        if pins:
            self.pins = pins
        else:
            # Assuming standard ComponentItem size of 100x50
            # Pin 1 (Entry): Left edge, middle height
            # Pin 2 (Exit): Right edge, middle height
            self.pins = [
                Pin(name="1", direction=PinDirection.INPUT, rel_x=0, rel_y=25),
                Pin(name="2", direction=PinDirection.OUTPUT, rel_x=100, rel_y=25)
            ]

    def add_pin(self, pin: Pin) -> None:
        """Add a new pin to the component."""
        self.pins.append(pin)

    def update_parameter(self, key: str, value: Any) -> None:
        """Update a single parameter value."""
        self.parameters[key] = value

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Return a parameter value by key."""
        return self.parameters.get(key, default)

    def all_parameters(self):
        """Return all parameter key-value pairs (view object)."""
        return self.parameters.items()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ref": self.ref,
            "comp_type": self.type,
            "parameters": self.parameters,
            "pins": [{"name": p.name, "x": p.rel_x, "y": p.rel_y} for p in self.pins]
        }