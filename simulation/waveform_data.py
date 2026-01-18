# simulation/waveform_data.py
"""
Waveform Data Structures — Containers for simulation results.

This module provides data structures for storing, manipulating, and
querying simulation waveform data from SPICE analyses.
"""

from typing import Dict, List, Optional, Tuple, Union, Iterator
from dataclasses import dataclass, field
from enum import Enum
import math


class WaveformType(Enum):
    """Types of waveform data."""
    VOLTAGE = "voltage"
    CURRENT = "current"
    POWER = "power"
    FREQUENCY = "frequency"
    TIME = "time"
    DC_SWEEP = "dc_sweep"


class AxisType(Enum):
    """Types of X-axis data."""
    TIME = "time"
    FREQUENCY = "frequency"
    DC_VALUE = "dc_value"
    INDEX = "index"


@dataclass
class WaveformPoint:
    """A single point in a waveform."""
    x: float
    y: float

    def __iter__(self):
        yield self.x
        yield self.y


@dataclass
class Waveform:
    """
    Represents a single waveform (e.g., voltage at a node over time).

    Attributes:
        name:  Identifier for this waveform (e.g., "V(N1)", "I(R1)")
        waveform_type:  Type of data (voltage, current, etc.)
        unit: Unit of measurement (V, A, W, etc.)
        x_data: X-axis values (time, frequency, etc.)
        y_data: Y-axis values (voltage, current, etc.)
        x_unit: Unit for X-axis
        x_type: Type of X-axis data
    """
    name: str
    waveform_type: WaveformType
    unit: str
    x_data: List[float] = field(default_factory=list)
    y_data: List[float] = field(default_factory=list)
    x_unit: str = "s"
    x_type: AxisType = AxisType.TIME

    # Metadata
    color: Optional[str] = None
    visible: bool = True

    def __post_init__(self):
        """Validate that x and y data have the same length."""
        if len(self.x_data) != len(self.y_data):
            raise ValueError(
                f"x_data and y_data must have same length:  "
                f"{len(self.x_data)} != {len(self.y_data)}"
            )

    def __len__(self) -> int:
        """Returns the number of data points."""
        return len(self.x_data)

    def __getitem__(self, index: int) -> WaveformPoint:
        """Returns a point at the given index."""
        return WaveformPoint(self.x_data[index], self.y_data[index])

    def __iter__(self) -> Iterator[WaveformPoint]:
        """Iterates over all points in the waveform."""
        for i in range(len(self)):
            yield self[i]

    @property
    def is_empty(self) -> bool:
        """Returns True if the waveform has no data."""
        return len(self.x_data) == 0

    @property
    def x_min(self) -> Optional[float]:
        """Returns the minimum X value."""
        return min(self.x_data) if self.x_data else None

    @property
    def x_max(self) -> Optional[float]:
        """Returns the maximum X value."""
        return max(self.x_data) if self.x_data else None

    @property
    def y_min(self) -> Optional[float]:
        """Returns the minimum Y value."""
        return min(self.y_data) if self.y_data else None

    @property
    def y_max(self) -> Optional[float]:
        """Returns the maximum Y value."""
        return max(self.y_data) if self.y_data else None

    @property
    def y_peak_to_peak(self) -> Optional[float]:
        """Returns the peak-to-peak amplitude."""
        if self.y_min is not None and self.y_max is not None:
            return self.y_max - self.y_min
        return None

    @property
    def y_average(self) -> Optional[float]:
        """Returns the average Y value."""
        if self.y_data:
            return sum(self.y_data) / len(self.y_data)
        return None

    @property
    def y_rms(self) -> Optional[float]:
        """Returns the RMS (root mean square) value."""
        if self.y_data:
            squares = [y * y for y in self.y_data]
            return math.sqrt(sum(squares) / len(squares))
        return None

    def get_value_at_x(self, x: float) -> Optional[float]:
        """
        Returns the interpolated Y value at a given X position.
        Uses linear interpolation between nearest points.
        """
        if not self.x_data:
            return None

        # Find the two nearest points
        for i in range(len(self.x_data) - 1):
            if self.x_data[i] <= x <= self.x_data[i + 1]:
                # Linear interpolation
                x1, x2 = self.x_data[i], self.x_data[i + 1]
                y1, y2 = self.y_data[i], self.y_data[i + 1]

                if x2 == x1:
                    return y1

                t = (x - x1) / (x2 - x1)
                return y1 + t * (y2 - y1)

        # X is outside the range
        if x <= self.x_data[0]:
            return self.y_data[0]
        elif x >= self.x_data[-1]:
            return self.y_data[-1]

        return None

    def get_slice(self, x_start: float, x_end: float) -> 'Waveform':
        """Returns a new waveform containing only data within the X range."""
        new_x = []
        new_y = []

        for i, x in enumerate(self.x_data):
            if x_start <= x <= x_end:
                new_x.append(x)
                new_y.append(self.y_data[i])

        return Waveform(
            name=self.name,
            waveform_type=self.waveform_type,
            unit=self.unit,
            x_data=new_x,
            y_data=new_y,
            x_unit=self.x_unit,
            x_type=self.x_type,
            color=self.color,
            visible=self.visible
        )

    def resample(self, num_points: int) -> 'Waveform':
        """Returns a new waveform resampled to the specified number of points."""
        if len(self) <= num_points or len(self) < 2:
            return self

        x_min, x_max = self.x_min, self.x_max
        step = (x_max - x_min) / (num_points - 1)

        new_x = [x_min + i * step for i in range(num_points)]
        new_y = [self.get_value_at_x(x) for x in new_x]

        return Waveform(
            name=self.name,
            waveform_type=self.waveform_type,
            unit=self.unit,
            x_data=new_x,
            y_data=new_y,
            x_unit=self.x_unit,
            x_type=self.x_type,
            color=self.color,
            visible=self.visible
        )

    def to_dict(self) -> Dict:
        """Serializes the waveform to a dictionary."""
        return {
            "name": self.name,
            "waveform_type": self.waveform_type.value,
            "unit": self.unit,
            "x_data": self.x_data,
            "y_data": self.y_data,
            "x_unit": self.x_unit,
            "x_type": self.x_type.value,
            "color": self.color,
            "visible": self.visible
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Waveform':
        """Deserializes a waveform from a dictionary."""
        return cls(
            name=data["name"],
            waveform_type=WaveformType(data["waveform_type"]),
            unit=data["unit"],
            x_data=data["x_data"],
            y_data=data["y_data"],
            x_unit=data.get("x_unit", "s"),
            x_type=AxisType(data.get("x_type", "time")),
            color=data.get("color"),
            visible=data.get("visible", True)
        )


@dataclass
class WaveformGroup:
    """
    A collection of related waveforms sharing the same X-axis.

    For example, all node voltages from a transient analysis.
    """
    name: str
    x_type: AxisType
    x_unit: str
    x_data: List[float] = field(default_factory=list)
    waveforms: Dict[str, Waveform] = field(default_factory=dict)

    def add_waveform(
            self,
            name: str,
            y_data: List[float],
            waveform_type: WaveformType = WaveformType.VOLTAGE,
            unit: str = "V",
            color: Optional[str] = None
    ) -> Waveform:
        """Adds a new waveform to the group."""
        if len(y_data) != len(self.x_data):
            raise ValueError(
                f"y_data length ({len(y_data)}) must match "
                f"x_data length ({len(self.x_data)})"
            )

        waveform = Waveform(
            name=name,
            waveform_type=waveform_type,
            unit=unit,
            x_data=self.x_data.copy(),
            y_data=y_data,
            x_unit=self.x_unit,
            x_type=self.x_type,
            color=color
        )
        self.waveforms[name] = waveform
        return waveform

    def get_waveform(self, name: str) -> Optional[Waveform]:
        """Returns a waveform by name."""
        return self.waveforms.get(name)

    def remove_waveform(self, name: str) -> bool:
        """Removes a waveform by name. Returns True if removed."""
        if name in self.waveforms:
            del self.waveforms[name]
            return True
        return False

    def get_all_waveforms(self) -> List[Waveform]:
        """Returns all waveforms in the group."""
        return list(self.waveforms.values())

    def get_visible_waveforms(self) -> List[Waveform]:
        """Returns only visible waveforms."""
        return [w for w in self.waveforms.values() if w.visible]

    @property
    def x_min(self) -> Optional[float]:
        """Returns the minimum X value."""
        return min(self.x_data) if self.x_data else None

    @property
    def x_max(self) -> Optional[float]:
        """Returns the maximum X value."""
        return max(self.x_data) if self.x_data else None

    @property
    def y_min(self) -> Optional[float]:
        """Returns the minimum Y value across all waveforms."""
        mins = [w.y_min for w in self.waveforms.values() if w.y_min is not None]
        return min(mins) if mins else None

    @property
    def y_max(self) -> Optional[float]:
        """Returns the maximum Y value across all waveforms."""
        maxs = [w.y_max for w in self.waveforms.values() if w.y_max is not None]
        return max(maxs) if maxs else None

    def __len__(self) -> int:
        """Returns the number of waveforms in the group."""
        return len(self.waveforms)

    def __contains__(self, name: str) -> bool:
        """Checks if a waveform exists in the group."""
        return name in self.waveforms


@dataclass
class OperatingPointData:
    """
    Container for DC operating point analysis results.

    Stores node voltages and branch currents at DC equilibrium.
    """
    node_voltages: Dict[str, float] = field(default_factory=dict)
    branch_currents: Dict[str, float] = field(default_factory=dict)

    def get_voltage(self, node: str) -> Optional[float]:
        """Returns the voltage at a node."""
        return self.node_voltages.get(node)

    def get_current(self, component: str) -> Optional[float]:
        """Returns the current through a component."""
        return self.branch_currents.get(component)

    def get_power(self, voltage_node: str, current_component: str) -> Optional[float]:
        """Calculates power from voltage and current."""
        v = self.get_voltage(voltage_node)
        i = self.get_current(current_component)
        if v is not None and i is not None:
            return v * i
        return None

    def get_all_nodes(self) -> List[str]:
        """Returns all node names."""
        return list(self.node_voltages.keys())

    def get_all_components(self) -> List[str]:
        """Returns all component names with current data."""
        return list(self.branch_currents.keys())

    def to_dict(self) -> Dict:
        """Serializes to a dictionary."""
        return {
            "node_voltages": self.node_voltages,
            "branch_currents": self.branch_currents
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'OperatingPointData':
        """Deserializes from a dictionary."""
        return cls(
            node_voltages=data.get("node_voltages", {}),
            branch_currents=data.get("branch_currents", {})
        )


@dataclass
class SimulationData:
    """
    Top-level container for all simulation results.

    Holds data from one or more analyses (OP, transient, AC, DC sweep).
    """
    title: str = "Untitled Simulation"

    # Operating point results
    operating_point: Optional[OperatingPointData] = None

    # Waveform groups for different analyses
    transient: Optional[WaveformGroup] = None
    ac_analysis: Optional[WaveformGroup] = None
    dc_sweep: Optional[WaveformGroup] = None

    # Metadata
    timestamp: Optional[str] = None
    netlist: Optional[str] = None

    def has_operating_point(self) -> bool:
        """Returns True if operating point data exists."""
        return self.operating_point is not None

    def has_transient(self) -> bool:
        """Returns True if transient data exists."""
        return self.transient is not None and len(self.transient) > 0

    def has_ac_analysis(self) -> bool:
        """Returns True if AC analysis data exists."""
        return self.ac_analysis is not None and len(self.ac_analysis) > 0

    def has_dc_sweep(self) -> bool:
        """Returns True if DC sweep data exists."""
        return self.dc_sweep is not None and len(self.dc_sweep) > 0

    def get_available_analyses(self) -> List[str]:
        """Returns a list of available analysis types."""
        analyses = []
        if self.has_operating_point():
            analyses.append("operating_point")
        if self.has_transient():
            analyses.append("transient")
        if self.has_ac_analysis():
            analyses.append("ac_analysis")
        if self.has_dc_sweep():
            analyses.append("dc_sweep")
        return analyses

    def get_all_node_names(self) -> List[str]:
        """Returns all unique node names across all analyses."""
        nodes = set()

        if self.operating_point:
            nodes.update(self.operating_point.get_all_nodes())

        if self.transient:
            for name in self.transient.waveforms:
                if name.upper().startswith("V("):
                    nodes.add(name)

        if self.ac_analysis:
            for name in self.ac_analysis.waveforms:
                if name.upper().startswith("V("):
                    nodes.add(name)

        if self.dc_sweep:
            for name in self.dc_sweep.waveforms:
                if name.upper().startswith("V("):
                    nodes.add(name)

        return sorted(list(nodes))

    def clear(self) -> None:
        """Clears all simulation data."""
        self.operating_point = None
        self.transient = None
        self.ac_analysis = None
        self.dc_sweep = None

    def to_dict(self) -> Dict:
        """Serializes all simulation data to a dictionary."""
        data = {
            "title": self.title,
            "timestamp": self.timestamp,
            "netlist": self.netlist
        }

        if self.operating_point:
            data["operating_point"] = self.operating_point.to_dict()

        if self.transient:
            data["transient"] = {
                "name": self.transient.name,
                "x_type": self.transient.x_type.value,
                "x_unit": self.transient.x_unit,
                "x_data": self.transient.x_data,
                "waveforms": {
                    name: wf.to_dict()
                    for name, wf in self.transient.waveforms.items()
                }
            }

        if self.ac_analysis:
            data["ac_analysis"] = {
                "name": self.ac_analysis.name,
                "x_type": self.ac_analysis.x_type.value,
                "x_unit": self.ac_analysis.x_unit,
                "x_data": self.ac_analysis.x_data,
                "waveforms": {
                    name: wf.to_dict()
                    for name, wf in self.ac_analysis.waveforms.items()
                }
            }

        if self.dc_sweep:
            data["dc_sweep"] = {
                "name": self.dc_sweep.name,
                "x_type": self.dc_sweep.x_type.value,
                "x_unit": self.dc_sweep.x_unit,
                "x_data": self.dc_sweep.x_data,
                "waveforms": {
                    name: wf.to_dict()
                    for name, wf in self.dc_sweep.waveforms.items()
                }
            }

        return data

    @classmethod
    def from_simulation_result(cls, result, title: str = "Simulation") -> 'SimulationData':
        """
        Creates SimulationData from a SpiceRunner SimulationResult.

        Args:
            result: SimulationResult from SpiceRunner
            title: Title for the simulation data

        Returns:
            SimulationData:  Populated simulation data container
        """
        from simulation.spice_runner import AnalysisType

        sim_data = cls(title=title)

        if result.analysis_type == AnalysisType.OPERATING_POINT:
            sim_data.operating_point = OperatingPointData(
                node_voltages=dict(result.operating_point),
                branch_currents=dict(result.branch_currents)
            )

        elif result.analysis_type == AnalysisType.TRANSIENT:
            sim_data.transient = WaveformGroup(
                name="Transient Analysis",
                x_type=AxisType.TIME,
                x_unit="s",
                x_data=list(result.time)
            )

            for node_name, voltages in result.node_voltages.items():
                sim_data.transient.add_waveform(
                    name=f"V({node_name})",
                    y_data=list(voltages),
                    waveform_type=WaveformType.VOLTAGE,
                    unit="V"
                )

            for comp_name, currents in result.branch_currents.items():
                sim_data.transient.add_waveform(
                    name=f"I({comp_name})",
                    y_data=list(currents),
                    waveform_type=WaveformType.CURRENT,
                    unit="A"
                )

        elif result.analysis_type == AnalysisType.AC_ANALYSIS:
            sim_data.ac_analysis = WaveformGroup(
                name="AC Analysis",
                x_type=AxisType.FREQUENCY,
                x_unit="Hz",
                x_data=list(result.frequency)
            )

            for node_name, voltages in result.node_voltages.items():
                sim_data.ac_analysis.add_waveform(
                    name=f"V({node_name})",
                    y_data=list(voltages),
                    waveform_type=WaveformType.VOLTAGE,
                    unit="V"
                )

        elif result.analysis_type == AnalysisType.DC_SWEEP:
            sim_data.dc_sweep = WaveformGroup(
                name="DC Sweep",
                x_type=AxisType.DC_VALUE,
                x_unit="V",
                x_data=list(result.time)  # DC sweep values stored in time
            )

            for node_name, voltages in result.node_voltages.items():
                sim_data.dc_sweep.add_waveform(
                    name=f"V({node_name})",
                    y_data=list(voltages),
                    waveform_type=WaveformType.VOLTAGE,
                    unit="V"
                )

        return sim_data


# Default color palette for waveforms
WAVEFORM_COLORS = [
    "#FF6B6B",  # Red
    "#4ECDC4",  # Teal
    "#45B7D1",  # Blue
    "#96CEB4",  # Green
    "#FFEAA7",  # Yellow
    "#DDA0DD",  # Plum
    "#98D8C8",  # Mint
    "#F7DC6F",  # Gold
    "#BB8FCE",  # Purple
    "#85C1E9",  # Sky blue
]


def get_waveform_color(index: int) -> str:
    """Returns a color from the palette based on index."""
    return WAVEFORM_COLORS[index % len(WAVEFORM_COLORS)]