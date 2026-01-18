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
    "InvalidNetlistError"
]