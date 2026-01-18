# simulation/spice_runner.py
"""
SPICE Runner — Executes SPICE simulations via PySpice/ngspice.

This module provides the interface between the netlist generator
and the ngspice simulation engine, handling simulation execution
and result parsing.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import tempfile
import os


class AnalysisType(Enum):
    """Types of SPICE analyses supported."""
    OPERATING_POINT = "op"  # DC operating point (. op)
    DC_SWEEP = "dc"  # DC sweep analysis (. dc)
    AC_ANALYSIS = "ac"  # AC frequency response (.ac)
    TRANSIENT = "tran"  # Time-domain transient (. tran)


class SimulationError(Exception):
    """Base exception for simulation errors."""
    pass


class NgspiceNotFoundError(SimulationError):
    """Raised when ngspice is not installed or not found."""
    pass


class SimulationFailedError(SimulationError):
    """Raised when the simulation fails to complete."""

    def __init__(self, message: str, spice_output: str = ""):
        self.spice_output = spice_output
        super().__init__(message)


class InvalidNetlistError(SimulationError):
    """Raised when the netlist is invalid."""
    pass


@dataclass
class AnalysisConfig:
    """Configuration for a SPICE analysis."""
    analysis_type: AnalysisType

    # Transient analysis parameters
    step_time: float = 1e-6  # Time step (seconds)
    stop_time: float = 1e-3  # End time (seconds)
    start_time: float = 0.0  # Start time (seconds)

    # DC sweep parameters
    source_name: str = ""  # Source to sweep (e.g., "V1")
    start_value: float = 0.0  # Sweep start value
    stop_value: float = 5.0  # Sweep stop value
    increment: float = 0.1  # Sweep increment

    # AC analysis parameters
    num_points: int = 100  # Number of frequency points
    start_freq: float = 1.0  # Start frequency (Hz)
    stop_freq: float = 1e6  # Stop frequency (Hz)
    variation: str = "dec"  # Variation type:  "dec", "oct", "lin"

    def to_spice_command(self) -> str:
        """Converts the analysis config to a SPICE command."""
        if self.analysis_type == AnalysisType.OPERATING_POINT:
            return ". OP"

        elif self.analysis_type == AnalysisType.TRANSIENT:
            return f".TRAN {self.step_time} {self.stop_time} {self.start_time}"

        elif self.analysis_type == AnalysisType.DC_SWEEP:
            return f".DC {self.source_name} {self.start_value} {self.stop_value} {self.increment}"

        elif self.analysis_type == AnalysisType.AC_ANALYSIS:
            return f".AC {self.variation.upper()} {self.num_points} {self.start_freq} {self.stop_freq}"

        else:
            raise ValueError(f"Unknown analysis type: {self.analysis_type}")


@dataclass
class SimulationResult:
    """Container for simulation results."""
    success: bool
    analysis_type: AnalysisType

    # Time/frequency vector (x-axis)
    time: List[float] = field(default_factory=list)
    frequency: List[float] = field(default_factory=list)

    # Node voltages:  node_name -> list of values
    node_voltages: Dict[str, List[float]] = field(default_factory=dict)

    # Branch currents: component_name -> list of values
    branch_currents: Dict[str, List[float]] = field(default_factory=dict)

    # Operating point results (DC values)
    operating_point: Dict[str, float] = field(default_factory=dict)

    # Raw SPICE output for debugging
    raw_output: str = ""

    # Error message if simulation failed
    error_message: str = ""

    def get_voltage(self, node: str) -> Optional[List[float]]:
        """Returns the voltage waveform for a node."""
        return self.node_voltages.get(node)

    def get_current(self, component: str) -> Optional[List[float]]:
        """Returns the current waveform through a component."""
        return self.branch_currents.get(component)

    def get_node_names(self) -> List[str]:
        """Returns all available node names."""
        return list(self.node_voltages.keys())

    def get_op_voltage(self, node: str) -> Optional[float]:
        """Returns the DC operating point voltage for a node."""
        return self.operating_point.get(node)


class SpiceRunner:
    """
    Executes SPICE simulations using PySpice/ngspice.

    This class handles:
    - Ngspice availability detection
    - Netlist preparation with analysis commands
    - Simulation execution
    - Result parsing and formatting
    """

    def __init__(self):
        self._ngspice_available: Optional[bool] = None
        self._pyspice_available: Optional[bool] = None
        self._last_netlist: str = ""
        self._last_result: Optional[SimulationResult] = None

    def check_ngspice_available(self) -> bool:
        """
        Checks if ngspice is installed and accessible.

        Returns:
            bool: True if ngspice is available, False otherwise.
        """
        if self._ngspice_available is not None:
            return self._ngspice_available

        # Try importing PySpice
        try:
            import PySpice
            from PySpice.Spice.NgSpice.Shared import NgSpiceShared
            self._pyspice_available = True
        except ImportError:
            self._pyspice_available = False
            self._ngspice_available = self._check_ngspice_cli()
            return self._ngspice_available

        # Try to initialize ngspice
        try:
            ngspice = NgSpiceShared.new_instance()
            self._ngspice_available = True
        except Exception:
            # Try command-line ngspice as fallback
            self._ngspice_available = self._check_ngspice_cli()

        return self._ngspice_available

    def _check_ngspice_cli(self) -> bool:
        """Checks if ngspice is available via command line."""
        import subprocess
        try:
            result = subprocess.run(
                ["ngspice", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def run_simulation(
            self,
            netlist: str,
            analysis: AnalysisConfig,
            probe_nodes: Optional[List[str]] = None
    ) -> SimulationResult:
        """
        Runs a SPICE simulation with the given netlist and analysis.

        Args:
            netlist: The SPICE netlist string.
            analysis: The analysis configuration.
            probe_nodes: Optional list of specific nodes to probe.
                        If None, all nodes are probed.

        Returns:
            SimulationResult: The simulation results.

        Raises:
            NgspiceNotFoundError: If ngspice is not available.
            SimulationFailedError: If the simulation fails.
        """
        if not self.check_ngspice_available():
            raise NgspiceNotFoundError(
                "ngspice is not installed.  Please install ngspice and PySpice:\n"
                "  pip install PySpice\n"
                "  # On Ubuntu/Debian:  sudo apt install ngspice\n"
                "  # On macOS:  brew install ngspice\n"
                "  # On Windows: Download from ngspice.sourceforge.io"
            )

        # Prepare the netlist with analysis commands
        full_netlist = self._prepare_netlist(netlist, analysis, probe_nodes)
        self._last_netlist = full_netlist

        # Try PySpice first, fall back to CLI
        if self._pyspice_available:
            try:
                return self._run_with_pyspice(full_netlist, analysis)
            except Exception as e:
                # Fall back to CLI mode
                return self._run_with_cli(full_netlist, analysis)
        else:
            return self._run_with_cli(full_netlist, analysis)

    def _prepare_netlist(
            self,
            netlist: str,
            analysis: AnalysisConfig,
            probe_nodes: Optional[List[str]] = None
    ) -> str:
        """Prepares the netlist with analysis and control commands."""
        lines = netlist.split("\n")

        # Find the . END statement and insert before it
        end_index = -1
        for i, line in enumerate(lines):
            if line.strip().upper() == ".END":
                end_index = i
                break

        # Build analysis commands
        analysis_lines = []
        analysis_lines.append("")
        analysis_lines.append("* --- Analysis Commands ---")
        analysis_lines.append(analysis.to_spice_command())

        # Add control block for saving data
        analysis_lines.append("")
        analysis_lines.append(". CONTROL")
        analysis_lines.append("run")

        # Save all node voltages or specific probes
        if probe_nodes:
            for node in probe_nodes:
                if node != "0":  # Don't probe ground
                    analysis_lines.append(f"print v({node})")
        else:
            analysis_lines.append("print all")

        analysis_lines.append(". ENDC")
        analysis_lines.append("")

        # Insert analysis commands before . END
        if end_index >= 0:
            lines = lines[:end_index] + analysis_lines + lines[end_index:]
        else:
            lines.extend(analysis_lines)
            lines.append(". END")

        return "\n".join(lines)

    def _run_with_pyspice(
            self,
            netlist: str,
            analysis: AnalysisConfig
    ) -> SimulationResult:
        """Runs simulation using PySpice's ngspice shared library."""
        from PySpice.Spice.NgSpice.Shared import NgSpiceShared
        from PySpice.Spice.Parser import SpiceParser

        result = SimulationResult(
            success=False,
            analysis_type=analysis.analysis_type
        )

        try:
            # Parse the netlist
            parser = SpiceParser(source=netlist)
            circuit = parser.build_circuit()

            # Get the simulator
            simulator = circuit.simulator(
                temperature=25,
                nominal_temperature=25
            )

            # Run the appropriate analysis
            if analysis.analysis_type == AnalysisType.OPERATING_POINT:
                sim_result = simulator.operating_point()
                result.success = True

                # Extract node voltages
                for node in sim_result.nodes.values():
                    result.operating_point[str(node)] = float(node)

            elif analysis.analysis_type == AnalysisType.TRANSIENT:
                sim_result = simulator.transient(
                    step_time=analysis.step_time,
                    end_time=analysis.stop_time,
                    start_time=analysis.start_time
                )
                result.success = True
                result.time = list(sim_result.time)

                # Extract node voltages
                for node_name, node_data in sim_result.nodes.items():
                    result.node_voltages[node_name] = list(node_data)

            elif analysis.analysis_type == AnalysisType.AC_ANALYSIS:
                sim_result = simulator.ac(
                    start_frequency=analysis.start_freq,
                    stop_frequency=analysis.stop_freq,
                    number_of_points=analysis.num_points,
                    variation=analysis.variation
                )
                result.success = True
                result.frequency = list(sim_result.frequency)

                # Extract node voltages (complex values - store magnitude)
                for node_name, node_data in sim_result.nodes.items():
                    result.node_voltages[node_name] = [abs(v) for v in node_data]

            elif analysis.analysis_type == AnalysisType.DC_SWEEP:
                # Parse source name to get the sweep source
                sim_result = simulator.dc(
                    **{analysis.source_name: slice(
                        analysis.start_value,
                        analysis.stop_value,
                        analysis.increment
                    )}
                )
                result.success = True

                # The sweep values become the x-axis
                result.time = list(sim_result[analysis.source_name])

                # Extract node voltages
                for node_name, node_data in sim_result.nodes.items():
                    result.node_voltages[node_name] = list(node_data)

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.raw_output = netlist

        return result

    def _run_with_cli(
            self,
            netlist: str,
            analysis: AnalysisConfig
    ) -> SimulationResult:
        """Runs simulation using ngspice command-line interface."""
        import subprocess

        result = SimulationResult(
            success=False,
            analysis_type=analysis.analysis_type
        )

        # Write netlist to temp file
        with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='. cir',
                delete=False
        ) as f:
            f.write(netlist)
            netlist_path = f.name

        try:
            # Run ngspice in batch mode
            proc = subprocess.run(
                ["ngspice", "-b", netlist_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            result.raw_output = proc.stdout + proc.stderr

            if proc.returncode == 0:
                result.success = True
                # Parse the output
                self._parse_cli_output(result, proc.stdout, analysis)
            else:
                result.success = False
                result.error_message = f"ngspice exited with code {proc.returncode}"

        except subprocess.TimeoutExpired:
            result.success = False
            result.error_message = "Simulation timed out after 30 seconds"
        except Exception as e:
            result.success = False
            result.error_message = str(e)
        finally:
            # Clean up temp file
            try:
                os.unlink(netlist_path)
            except OSError:
                pass

        return result

    def _parse_cli_output(
            self,
            result: SimulationResult,
            output: str,
            analysis: AnalysisConfig
    ) -> None:
        """Parses ngspice CLI output to extract simulation data."""
        lines = output.split("\n")

        current_node = None
        values = []

        for line in lines:
            line = line.strip()

            # Look for node voltage output lines
            # Format: "v(node) = value" or "node = value"
            if "=" in line and ("v(" in line.lower() or "i(" in line.lower()):
                parts = line.split("=")
                if len(parts) == 2:
                    name = parts[0].strip()
                    try:
                        value = float(parts[1].strip().split()[0])

                        # Clean up the name
                        if name.lower().startswith("v("):
                            node_name = name[2:-1] if name.endswith(")") else name[2:]
                            if analysis.analysis_type == AnalysisType.OPERATING_POINT:
                                result.operating_point[node_name] = value
                            else:
                                if node_name not in result.node_voltages:
                                    result.node_voltages[node_name] = []
                                result.node_voltages[node_name].append(value)
                        elif name.lower().startswith("i("):
                            comp_name = name[2:-1] if name.endswith(")") else name[2:]
                            if comp_name not in result.branch_currents:
                                result.branch_currents[comp_name] = []
                            result.branch_currents[comp_name].append(value)
                    except ValueError:
                        continue

    def get_last_netlist(self) -> str:
        """Returns the last netlist that was simulated."""
        return self._last_netlist

    def get_last_result(self) -> Optional[SimulationResult]:
        """Returns the last simulation result."""
        return self._last_result

    def get_supported_analyses(self) -> List[AnalysisType]:
        """Returns a list of supported analysis types."""
        return list(AnalysisType)

    @staticmethod
    def create_transient_config(
            step_time: float = 1e-6,
            stop_time: float = 1e-3,
            start_time: float = 0.0
    ) -> AnalysisConfig:
        """Creates a transient analysis configuration."""
        return AnalysisConfig(
            analysis_type=AnalysisType.TRANSIENT,
            step_time=step_time,
            stop_time=stop_time,
            start_time=start_time
        )

    @staticmethod
    def create_dc_sweep_config(
            source_name: str,
            start_value: float = 0.0,
            stop_value: float = 5.0,
            increment: float = 0.1
    ) -> AnalysisConfig:
        """Creates a DC sweep analysis configuration."""
        return AnalysisConfig(
            analysis_type=AnalysisType.DC_SWEEP,
            source_name=source_name,
            start_value=start_value,
            stop_value=stop_value,
            increment=increment
        )

    @staticmethod
    def create_ac_config(
            start_freq: float = 1.0,
            stop_freq: float = 1e6,
            num_points: int = 100,
            variation: str = "dec"
    ) -> AnalysisConfig:
        """Creates an AC analysis configuration."""
        return AnalysisConfig(
            analysis_type=AnalysisType.AC_ANALYSIS,
            start_freq=start_freq,
            stop_freq=stop_freq,
            num_points=num_points,
            variation=variation
        )

    @staticmethod
    def create_op_config() -> AnalysisConfig:
        """Creates an operating point analysis configuration."""
        return AnalysisConfig(analysis_type=AnalysisType.OPERATING_POINT)
