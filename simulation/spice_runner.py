# simulation/spice_runner.py
"""
SPICE Runner — Executes SPICE simulations via PySpice/ngspice.

This module provides the interface between the netlist generator
and the ngspice simulation engine, handling simulation execution
and result parsing.
"""
import os
# 1. SET PATHS FIRST


# 2. NOW IMPORT THE REST
from PySpice.Spice.Parser import SpiceParser

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import os


class AnalysisType(Enum):
    """Types of SPICE analyses supported."""
    OPERATING_POINT = "op"  # DC operating point (.op)
    DC_SWEEP = "dc"  # DC sweep analysis (.dc)
    AC_ANALYSIS = "ac"  # AC frequency response (.ac)
    TRANSIENT = "tran"  # Time-domain transient (.tran)


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
            return ".OP"

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
        if self._ngspice_available is not None:
            return self._ngspice_available

        # 1.ATTEMPT TO SET LOCAL PATH (If you put the DLL in a 'lib' folder)
        # Get the absolute path to the folder containing this script
        base_path = Path(__file__).parent.parent.absolute()
        local_lib = base_path / "lib" / "ngspice.dll"

        if local_lib.exists():
            # Explicitly set the library path for PySpice
            os.environ["PYSPICE_LIBRARY_PATH"] = str(local_lib)

        # 2.Try importing PySpice
        try:
            import PySpice
            from PySpice.Spice.NgSpice.Shared import NgSpiceShared
            self._pyspice_available = True

            # Optional: Force load to verify the DLL actually works right now
            # This catches the error immediately instead of during simulation
            _ = NgSpiceShared.new_instance()

        except (ImportError, OSError, Exception) as e:
            # OSError is raised if the DLL is missing during load
            print(f"PySpice load failed: {e}")
            self._pyspice_available = False
            self._ngspice_available = self._check_ngspice_cli()
            return self._ngspice_available

        self._ngspice_available = True
        return True

    def _check_ngspice_cli(self) -> bool:
        """Actually checks if ngspice executable is in the system PATH."""
        import shutil
        return shutil.which("ngspice") is not None

    def run_simulation(self, netlist: str, analysis: AnalysisConfig,
                       probe_nodes: Optional[List[str]] = None) -> SimulationResult:
        # 1. Prepare the full netlist for the CLI
        full_netlist = self._prepare_netlist(netlist, analysis, probe_nodes)

        # 2. Try CLI first (it's more reliable on Python 3.14)
        try:
            if self._check_ngspice_cli():
                result = self._run_with_cli(full_netlist, analysis)
                return result
        except Exception as e:
            print(f"CLI simulation failed with exception: {e}. Trying PySpice...")

        # 3. Fallback to PySpice only if CLI isn't available
        if self._pyspice_available:
            result = self._run_with_pyspice(netlist, analysis)
            return result

        raise NgspiceNotFoundError("No simulation engine (CLI or DLL) is working.")

    def _prepare_netlist(
            self,
            netlist: str,
            analysis: AnalysisConfig,
            probe_nodes: Optional[List[str]] = None
    ) -> str:
        """Prepares the netlist with analysis and control commands."""
        lines = netlist.split("\n")

        # Find the .END statement and insert before it
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
        analysis_lines.append(".CONTROL")
        analysis_lines.append("run")

        # Save all node voltages or specific probes
        if probe_nodes:
            for node in probe_nodes:
                if node != "0":  # Don't probe ground
                    analysis_lines.append(f"print v({node})")
        else:
            analysis_lines.append("set filetype=ascii")
            analysis_lines.append("write sim.raw")
            analysis_lines.append("quit")

        analysis_lines.append(".ENDC")
        analysis_lines.append("")

        # Insert analysis commands before .END
        if end_index >= 0:
            lines = lines[:end_index] + analysis_lines + lines[end_index:]
        else:
            lines.extend(analysis_lines)
            lines.append(".END")

        return "\n".join(lines)

    def _run_with_pyspice(
            self,
            netlist: str,
            analysis: AnalysisConfig
    ) -> SimulationResult:
        """Runs simulation using PySpice's ngspice shared library."""

        clean_netlist = netlist
        if not netlist.startswith("TITLE"):
            clean_netlist = "TITLE\n" + netlist

        result = SimulationResult(
            success=False,
            analysis_type=analysis.analysis_type
        )

        try:
            # Parse the netlist
            parser = SpiceParser(source=clean_netlist)
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
        import tempfile
        import os

        result = SimulationResult(
            success=False,
            analysis_type=analysis.analysis_type
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.cir', delete=False) as f:
            f.write(netlist)
            netlist_path = f.name

        try:
            # 1. CHANGE THIS: Use the full path to your ngspice.exe
            # Example: r"C:\Spice64\bin\ngspice.exe"
            executable = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
            if not os.path.exists(executable):
                return SimulationResult(success=False, analysis_type=analysis.analysis_type,
                                        error_message=f"Executable not found at {executable}")

            proc = subprocess.run(
                [executable, "-b", "-n", netlist_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            # 2. COMBINE STDOUT AND STDERR
            # Ngspice often sends the table data to one and warnings to the other
            full_output = proc.stdout + "\n" + proc.stderr
            result.raw_output = full_output

            # 3. PARSE THE COMBINED OUTPUT
            # We parse even if returncode != 0 because Ngspice often returns 1 for minor warnings
            self._parse_output(result, analysis)

            if result.node_voltages or result.operating_point:
                result.success = True
            else:
                result.success = False
                result.error_message = f"No data parsed. Exit code: {proc.returncode}"

        except subprocess.TimeoutExpired:
            result.success = False
            result.error_message = "Simulation timed out after 30 seconds"
        except Exception as e:
            result.success = False
            result.error_message = str(e)
        finally:
            if os.path.exists(netlist_path):
                os.unlink(netlist_path)

        return result

    def _parse_output(self, result, analysis):
        raw_path = os.path.join(os.getcwd(), "sim.raw")
        if not os.path.exists(raw_path):
            result.success = False
            result.error_message = f"RAW file not found: {raw_path}"
        else:
            if analysis.analysis_type == AnalysisType.OPERATING_POINT:
                self._parse_op_raw_file(result, raw_path)
            elif analysis.analysis_type == AnalysisType.DC_SWEEP:
                self._parse_dc_raw_file(result, raw_path)
            elif analysis.analysis_type == AnalysisType.TRANSIENT:
                self._parse_tran_raw_file(result, raw_path)
            elif analysis.analysis_type == AnalysisType.AC_ANALYSIS:
                self._parse_ac_raw_file(result, raw_path)

    def _parse_op_raw_file(self, result, filename):
        with open(filename, "r") as f:
            lines = f.readlines()

        # Headers/variable discovery
        variable_names = []
        in_variables = False
        num_variables = 0
        data_start = None

        for line_no, line in enumerate(lines):
            s = line.strip()
            if s.startswith("No. Variables:"):
                num_variables = int(s.split()[-1])
            if s.startswith('Variables:'):
                in_variables = True
                continue
            if in_variables:
                if s.lower().startswith('values:'):
                    in_variables = False
                    data_start = line_no + 1
                    break
                if not s or ':' in s:
                    in_variables = False
                    continue
                parts = s.split()
                if len(parts) >= 2:
                    variable_names.append(parts[1])
                continue
            if s.lower().startswith('values:'):
                data_start = line_no + 1
                break

        if not num_variables or not variable_names:
            print('Did not detect required headers.')
            return

        if data_start is None:
            print('No Values section found! Cannot parse data.')
            return

        result.node_voltages = {}

        # Parse data: OP analysis has only one set of values
        value_lines = [line.strip() for line in lines[data_start:] if line.strip()]

        # LTspice might write single value per line, with or without indices
        values = []
        for val_line in value_lines:
            parts = val_line.split()
            if len(parts) == 2 and parts[0].isdigit():
                # Format: "0 <value>"
                values.append(float(parts[1]))
            elif len(parts) == 1:
                # Format: "<value>"
                try:
                    values.append(float(parts[0]))
                except ValueError:
                    values.append(None)
            else:
                # Unrecognized line
                continue

        if len(values) != len(variable_names):
            print("Warning: Mismatch between variables and parsed values.")
        for name, value in zip(variable_names, values):
            result.node_voltages[name] = value
        # For OP, no time axis
        result.time = None

    def _parse_dc_raw_file(self, result, filename):
        with open(filename, "r") as f:
            lines = f.readlines()

        variable_names = []
        in_variables = False
        num_variables = 0
        data_start = None

        # --- Header Parsing ---
        for line_no, line in enumerate(lines):
            s = line.strip()

            if s.startswith("No. Variables:"):
                num_variables = int(s.split()[-1])

            if s.startswith('Variables:'):
                in_variables = True
                continue

            if in_variables:
                if s.lower().startswith('values:'):
                    in_variables = False
                    data_start = line_no + 1
                    break

                # Using .split() without arguments handles any whitespace (tabs or spaces)
                parts = s.split()
                if len(parts) >= 2:
                    # parts[0] is index, parts[1] is name (e.g., 'v(v-sweep)')
                    var_name = parts[1]
                    variable_names.append(var_name)
                continue

            if s.lower().startswith('values:'):
                data_start = line_no + 1
                break

        # --- Data Parsing ---
        # Initialize dictionary with lists for each variable
        node_data = {name: [] for name in variable_names}

        value_lines = [line.strip() for line in lines[data_start:] if line.strip()]

        current_var_idx = 0
        point_count = 0

        for line in value_lines:
            parts = line.split()
            if not parts: continue

            try:
                # The value is the last part of the line
                val = float(parts[-1])
                var_name = variable_names[current_var_idx]
                node_data[var_name].append(val)

                current_var_idx += 1
                if current_var_idx >= num_variables:
                    current_var_idx = 0
                    point_count += 1
            except ValueError:
                continue

        # --- Mapping to Result Object ---
        result.node_voltages = node_data

        # IMPORTANT: Your app expects the X-axis in 'result.time'
        # In a DC sweep, the first variable (index 0) is the X-axis.
        sweep_name = variable_names[0]
        result.time = node_data[sweep_name]

    def _parse_tran_raw_file(self, result, filename):
        with open(filename, "r") as f:
            lines = f.readlines()

        # variable_names = ["time", "v(n3)", "v(n4)", "i(v1)"]
        variable_names = []
        in_variables = False
        num_variables = 0
        data_start = None

        for line_no, line in enumerate(lines):
            s = line.strip()
            if s.startswith("No. Variables:"):
                num_variables = int(s.split()[-1])
            if s.startswith('Variables:'):
                in_variables = True
                continue
            if in_variables:
                # Detect 'Values:' before skipping lines containing ':'
                if s.lower().startswith('values:'):
                    in_variables = False  # End variable-section
                    data_start = line_no + 1  # Start parsing after 'Values:'
                    break
                if not s or ':' in s:
                    in_variables = False
                    continue
                parts = s.split()
                if len(parts) >= 2:
                    variable_names.append(parts[1])
                continue

            if s.lower().startswith('values:'):
                data_start = line_no + 1  # Start parsing after 'Values:'
                break

        if not num_variables or not variable_names:
            print('Did not detect required headers.')
            return

        if data_start is None:
            print('No Values section found! Cannot parse data.')
            return

        result.time = []
        result.node_voltages = {name: [] for name in variable_names if name != "time"}

        i = data_start
        while i < len(lines):
            # Skip empty lines
            if not lines[i].strip():
                i += 1
                continue
            # First line: timestep idx and time value
            tokens = lines[i].split()
            if len(tokens) == 2 and tokens[0].isdigit():
                # Grab time value
                result.time.append(float(tokens[1]))
                values = []
                # For all remaining variables
                for var_idx in range(1, num_variables):
                    i += 1
                    # Check for out-of-bounds
                    if i < len(lines) and lines[i].strip():
                        values.append(float(lines[i]))
                    else:
                        values.append(None)
                # Assign values to respective variables
                for name, value in zip(variable_names[1:], values):
                    result.node_voltages[name].append(value)
                i += 1  # move to next (blank or next timestep)
            else:
                i += 1  # skip malformed line

    def _parse_ac_raw_file(self, result, raw_path):
        import math

        with open(raw_path, "r") as f:
            lines = f.readlines()

        # --- Locate Variables and Values sections ---
        variables = []
        n_vars = 0
        for i, line in enumerate(lines):
            if line.startswith("No. Variables:"):
                n_vars = int(line.partition(":")[2])
            if line.startswith("Variables:"):
                var_start = i + 1
                variables = [lines[j].split()[1].strip('"') for j in range(var_start, var_start + n_vars)]
            if line.startswith("Values:"):
                data_start = i + 1
                break

        num_points = int([l for l in lines if l.startswith("No. Points:")][0].partition(":")[2])

        i = data_start
        idx = 0
        while idx < num_points and i < len(lines):
            # skip blank lines
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i + n_vars - 1 >= len(lines):
                break  # not enough lines left for a full block

            block = []
            for j in range(n_vars):
                line = lines[i + j].strip()
                block.append(line)
            i += n_vars

            # Parse the data block
            if not block[0]:
                continue

            first_line = block[0].split()
            try:
                point_idx = int(first_line[0])
                freq_str = first_line[1]
                freq_real = float(freq_str.split(',')[0])
            except Exception as e:
                print(f"Failed to parse index/freq at idx={idx}: '{block[0]}' error: {e}")
                continue

            if len(result.frequency) <= point_idx:
                result.frequency.append(freq_real)

            for j in range(1, n_vars):
                varname = variables[j]
                raw_val = block[j]
                try:
                    r_str, im_str = raw_val.split(',')
                    r = float(r_str)
                    im = float(im_str)
                    mag = math.hypot(r, im)
                except Exception as e:
                    print(f"Could not parse value for '{varname}' at idx={point_idx}: '{raw_val}', error: {e}")
                    continue

                if varname not in result.node_voltages:
                    result.node_voltages[varname] = []
                result.node_voltages[varname].append(mag)
            idx += 1

        # After this, result.frequency and each result.node_voltages[var] should be length num_points!

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
