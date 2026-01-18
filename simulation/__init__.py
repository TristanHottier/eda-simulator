# simulation/__init__.py
"""
Simulation package for EDA Simulator.

This package provides the interface between the schematic editor
and the SPICE simulation backend (ngspice via PySpice).
"""

from simulation.netlist_generator import (
    NetlistGenerator,
    NetlistComponent,
    NetlistError,
    MissingGroundError,
    FloatingNodeError,
    InvalidComponentError
)

from simulation.spice_runner import (
    SpiceRunner,
    AnalysisType,
    AnalysisConfig,
    SimulationResult,
    SimulationError,
    NgspiceNotFoundError,
    SimulationFailedError,
    InvalidNetlistError
)

from simulation.waveform_data import (
    Waveform,
    WaveformType,
    WaveformPoint,
    WaveformGroup,
    AxisType,
    OperatingPointData,
    SimulationData,
    WAVEFORM_COLORS,
    get_waveform_color
)

__all__ = [
    # Netlist Generator
    "NetlistGenerator",
    "NetlistComponent",
    "NetlistError",
    "MissingGroundError",
    "FloatingNodeError",
    "InvalidComponentError",
    # SPICE Runner
    "SpiceRunner",
    "AnalysisType",
    "AnalysisConfig",
    "SimulationResult",
    "SimulationError",
    "NgspiceNotFoundError",
    "SimulationFailedError",
    "InvalidNetlistError",
    # Waveform Data
    "Waveform",
    "WaveformType",
    "WaveformPoint",
    "WaveformGroup",
    "AxisType",
    "OperatingPointData",
    "SimulationData",
    "WAVEFORM_COLORS",
    "get_waveform_color"
]