# core/component.py
from typing import List, Dict, Any, Optional
from core.pin import Pin, PinDirection


class Component:
    """
    Represents an electronic component in the schematic.
    Stores pins, parameters, and reference designator (ref).
    """

    DEFAULT_PARAMS = {
        "resistor": {"resistance": 1, "type": "resistor"},
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
            "BV": 5.6,               # breakdown voltage (only for zener)
            "IBV": 0.001             # reverse current at breakdown voltage (only for zener)
        },
        "ground": {"type": "ground"},
        "dc_voltage_source":  {"voltage": 5.0, "type": "dc_voltage_source"},
        "ac_voltage_source": {"voltage":  5.0, "frequency": 1000, "type": "ac_voltage_source"},
        "dc_current_source": {"current": 0.001, "type":  "dc_current_source"},
        "generic": {"type": "generic"},
        "transistor": {
            "family_type": "bjt",   # default family
            "type": "npn",          # default transistor type
            # For BJTs
            "IS": 1e-15,
            "BF": 100,
            "NF": 1.0,
            "VAF": 100,
            "IKF": 0.1,
            "CJE": 2e-12,
            "CJC": 1e-12,
            "TF": 0.5e-9,
            # For MOSFETs
            "KP": 50e-6,
            "LAMBDA": 0.02,
            "CGS": 1e-12,
            "CGD": 1e-12,
            "CBD":1e-12
        }
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

        if self.type == "transistor":
            family = self.parameters.get("transistor_family", "").lower()
            t_type = self.parameters.get("transistor_type", "").lower()

            # ------------------
            # BJT
            # ------------------
            if family == "bjt":
                # Common BJT defaults
                self.parameters.setdefault("IS", 1e-15)  # saturation current
                self.parameters.setdefault("BF", 100)  # forward beta
                self.parameters.setdefault("NF", 1.0)  # emission coefficient
                self.parameters.setdefault("VAF", 100)  # Early voltage
                self.parameters.setdefault("IKF", 0.1)  # beta roll-off current
                self.parameters.setdefault("CJE", 2e-12)  # base-emitter capacitance
                self.parameters.setdefault("CJC", 1e-12)  # base-collector capacitance
                self.parameters.setdefault("TF", 0.5e-9)  # forward transit time

                if t_type == "pnp":
                    # PNP usually mirrors NPN with polarity handled elsewhere
                    pass

            # ------------------
            # MOSFET
            # ------------------
            elif family == "mosfet":
                # Common MOSFET defaults
                self.parameters.setdefault("KP", 50e-6)  # transconductance parameter
                self.parameters.setdefault("LAMBDA", 0.02)  # channel-length modulation
                self.parameters.setdefault("CGS", 1e-12)
                self.parameters.setdefault("CGD", 1e-12)
                self.parameters.setdefault("CBD", 1e-12)

                if t_type == "nmos":
                    self.parameters.setdefault("VTO", 1.0)  # threshold voltage
                elif t_type == "pmos":
                    self.parameters.setdefault("VTO", -1.0)  # negative threshold
                    self.parameters.setdefault("KP", 25e-6)  # PMOS usually weaker

        # FIX: Automatically generate entry and exit pins if none are provided
        if pins:
            self.pins = pins
        else:
            # Ground component has only one pin at the top center
            if self.type == "ground":
                self.pins = [
                    Pin(name="1", direction=PinDirection.INPUT, rel_x=25, rel_y=0)
                ]
            # Voltage and current sources have vertical pin layout (2x1 grid: 50x100)
            elif self.type in ("dc_voltage_source", "ac_voltage_source", "dc_current_source"):
                self.pins = [
                    Pin(name="+", direction=PinDirection.OUTPUT, rel_x=25, rel_y=0),
                    Pin(name="-", direction=PinDirection.INPUT, rel_x=25, rel_y=100)
                ]
            # BJTs
            elif self.type == "transistor":
                transistor_type = self.parameters.get("type", "npn")
                if transistor_type in ("npn", "pnp"):
                    # BJT layout: Base (left), Collector (top), Emitter (bottom-right)
                    # Matches standard symbol with base on left, collector up, emitter down-right
                    self.pins = [
                        Pin(name="B", direction=PinDirection.INPUT, rel_x=0, rel_y=25),  # Base (left)
                        Pin(name="C", direction=PinDirection.INPUT, rel_x=65, rel_y=-4),  # Collector (top)
                        Pin(name="E", direction=PinDirection.OUTPUT, rel_x=65, rel_y=54)  # Emitter (bottom)
                    ]
                # MOSFETs (N-channel/P-channel)
                elif transistor_type in ("nmos", "pmos"):
                    # MOSFET layout: Gate (left), Drain (top), Source (bottom)
                    # Matches standard symbol with gate on left, drain up, source down
                    self.pins = [
                        Pin(name="G", direction=PinDirection.INPUT, rel_x=0, rel_y=25),  # Gate (left)
                        Pin(name="D", direction=PinDirection.INPUT, rel_x=50, rel_y=0),  # Drain (top)
                        Pin(name="S", direction=PinDirection.OUTPUT, rel_x=50, rel_y=50)  # Source (bottom)
                    ]
            else:
                # Standard components: Assuming standard ComponentItem size of 100x50
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
