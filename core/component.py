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
        "led": {"voltage_drop": 2.0, "type":  "led"},
        "inductor": {"inductance": 100, "type": "inductor"},
        "diode": {
            "type": "diode",
            "diode_type": "silicon",  # can be "silicon", "schottky", "zener"
            "IS": 1e-14,  # saturation current, default value for standard silicon
            "N": 1.0,  # ideality factor
            "TT": 0,  # transit time (switching, 0 for most non-schottky)
            # Zener-specific parameters (optional, for zener only)
            # "BV": 5.6,               # breakdown voltage (only for zener)
            # "IBV": 0.001             # reverse current at breakdown voltage (only for zener)
        },
        "ground": {"type": "ground"},
        "dc_voltage_source":  {"voltage": 5.0, "type": "dc_voltage_source"},
        "ac_voltage_source": {"voltage":  5.0, "frequency": 1000, "type": "ac_voltage_source"},
        "dc_current_source": {"current": 0.001, "type":  "dc_current_source"},
        "generic": {"type": "generic"}
    }

    def __init__(self, ref: str, pins: Optional[List[Pin]] = None,
                 parameters:  Optional[Dict[str, Any]] = None, comp_type: str = "generic"):
        self.ref = ref
        self.type = comp_type.lower()

        # Merge default parameters
        base_params = self.DEFAULT_PARAMS.get(self.type, self.DEFAULT_PARAMS["generic"])
        self.parameters = {**base_params, **(parameters or {})}

        if self.type == "diode":
            d_type = self.parameters.get("diode_type", "silicon").lower()
            if d_type == "schottky":
                self.parameters.setdefault("TT", 1e-9)  # example: 1 ns transit time
                self.parameters.setdefault("IS", 2e-14)  # typical Schottky IS
                self.parameters.setdefault("N", 1.05)  # typical Schottky N
            elif d_type == "zener":
                self.parameters.setdefault("IS", 5e-14)
                self.parameters.setdefault("N", 1.0)
                self.parameters.setdefault("BV", 5.6)  # default breakdown V for Zener
                self.parameters.setdefault("IBV", 1e-3)  # 1 mA at breakdown

        # FIX: Automatically generate entry and exit pins if none are provided
        if pins:
            self.pins = pins
        else:
            # Ground component has only one pin at the top center
            if self.type == "ground":
                self.pins = [
                    Pin(name="1", direction=PinDirection.INPUT, rel_x=25, rel_y=0)
                ]
            # Voltage and current sources have vertical pin layout (2x1 grid:  50x100)
            # Pin + (positive): top center
            # Pin - (negative): bottom center
            elif self.type in ("dc_voltage_source", "ac_voltage_source", "dc_current_source"):
                self.pins = [
                    Pin(name="+", direction=PinDirection.OUTPUT, rel_x=25, rel_y=0),
                    Pin(name="-", direction=PinDirection.INPUT, rel_x=25, rel_y=100)
                ]
            else:
                # Standard components:  Assuming standard ComponentItem size of 100x50
                # Pin 1 (Entry): Left edge, middle height
                # Pin 2 (Exit): Right edge, middle height
                self.pins = [
                    Pin(name="1", direction=PinDirection.INPUT, rel_x=0, rel_y=25),
                    Pin(name="2", direction=PinDirection.OUTPUT, rel_x=100, rel_y=25)
                ]

    def add_pin(self, pin: Pin) -> None:
        """Add a new pin to the component."""
        self.pins.append(pin)

    def update_parameter(self, key: str, value:  Any) -> None:
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
            "pins":  [{"name": p.name, "x": p.rel_x, "y": p.rel_y} for p in self.pins]
        }