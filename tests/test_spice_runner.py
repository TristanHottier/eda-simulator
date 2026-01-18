# tests/test_spice_runner.py
"""
Unit tests for the SPICE Runner.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from simulation.spice_runner import (
    SpiceRunner,
    AnalysisType,
    AnalysisConfig,
    SimulationResult,
    NgspiceNotFoundError
)


class TestAnalysisConfig(unittest.TestCase):
    """Tests for AnalysisConfig."""

    def test_operating_point_command(self):
        """Test operating point SPICE command."""
        config = AnalysisConfig(analysis_type=AnalysisType.OPERATING_POINT)
        result = config.to_spice_command()
        # Check that it contains .OP
        self.assertIn(".OP", result.replace(" ", ""))

    def test_transient_command(self):
        """Test transient analysis SPICE command."""
        config = AnalysisConfig(
            analysis_type=AnalysisType.TRANSIENT,
            step_time=1e-6,
            stop_time=1e-3,
            start_time=0.0
        )
        result = config.to_spice_command()
        self.assertIn(".TRAN", result.replace(" ", "").upper())

    def test_dc_sweep_command(self):
        """Test DC sweep analysis SPICE command."""
        config = AnalysisConfig(
            analysis_type=AnalysisType.DC_SWEEP,
            source_name="V1",
            start_value=0.0,
            stop_value=5.0,
            increment=0.1
        )
        result = config.to_spice_command()
        self.assertIn(".DC", result.replace(" ", ""))
        self.assertIn("V1", result)

    def test_ac_analysis_command(self):
        """Test AC analysis SPICE command."""
        config = AnalysisConfig(
            analysis_type=AnalysisType.AC_ANALYSIS,
            num_points=100,
            start_freq=1.0,
            stop_freq=1e6,
            variation="dec"
        )
        result = config.to_spice_command()
        self.assertIn(".AC", result.replace(" ", ""))
        self.assertIn("DEC", result.upper())
        self.assertIn("100", result)


class TestSimulationResult(unittest.TestCase):
    """Tests for SimulationResult."""

    def test_empty_result(self):
        """Test empty simulation result."""
        result = SimulationResult(
            success=False,
            analysis_type=AnalysisType.OPERATING_POINT
        )
        self.assertFalse(result.success)
        self.assertEqual(len(result.node_voltages), 0)

    def test_get_voltage(self):
        """Test getting voltage waveform."""
        result = SimulationResult(
            success=True,
            analysis_type=AnalysisType.TRANSIENT,
            node_voltages={"N1": [1.0, 2.0, 3.0]}
        )
        voltage = result.get_voltage("N1")
        self.assertEqual(voltage, [1.0, 2.0, 3.0])

    def test_get_voltage_nonexistent(self):
        """Test getting voltage for nonexistent node."""
        result = SimulationResult(
            success=True,
            analysis_type=AnalysisType.TRANSIENT
        )
        voltage = result.get_voltage("NONEXISTENT")
        self.assertIsNone(voltage)

    def test_get_node_names(self):
        """Test getting all node names."""
        result = SimulationResult(
            success=True,
            analysis_type=AnalysisType.TRANSIENT,
            node_voltages={"N1": [1.0], "N2": [2.0], "N3": [3.0]}
        )
        names = result.get_node_names()
        self.assertEqual(set(names), {"N1", "N2", "N3"})

    def test_get_op_voltage(self):
        """Test getting operating point voltage."""
        result = SimulationResult(
            success=True,
            analysis_type=AnalysisType.OPERATING_POINT,
            operating_point={"N1": 3.3, "N2": 1.65}
        )
        self.assertEqual(result.get_op_voltage("N1"), 3.3)
        self.assertEqual(result.get_op_voltage("N2"), 1.65)


class TestSpiceRunner(unittest.TestCase):
    """Tests for SpiceRunner."""

    def test_initialization(self):
        """Test runner initialization."""
        runner = SpiceRunner()
        self.assertIsNone(runner._ngspice_available)
        self.assertEqual(runner._last_netlist, "")

    def test_create_transient_config(self):
        """Test transient config factory method."""
        config = SpiceRunner.create_transient_config(
            step_time=1e-6,
            stop_time=1e-3
        )
        self.assertEqual(config.analysis_type, AnalysisType.TRANSIENT)
        self.assertEqual(config.step_time, 1e-6)
        self.assertEqual(config.stop_time, 1e-3)

    def test_create_dc_sweep_config(self):
        """Test DC sweep config factory method."""
        config = SpiceRunner.create_dc_sweep_config(
            source_name="V1",
            start_value=0,
            stop_value=10,
            increment=0.5
        )
        self.assertEqual(config.analysis_type, AnalysisType.DC_SWEEP)
        self.assertEqual(config.source_name, "V1")
        self.assertEqual(config.stop_value, 10)

    def test_create_ac_config(self):
        """Test AC analysis config factory method."""
        config = SpiceRunner.create_ac_config(
            start_freq=100,
            stop_freq=1e6,
            num_points=50
        )
        self.assertEqual(config.analysis_type, AnalysisType.AC_ANALYSIS)
        self.assertEqual(config.start_freq, 100)
        self.assertEqual(config.num_points, 50)

    def test_create_op_config(self):
        """Test operating point config factory method."""
        config = SpiceRunner.create_op_config()
        self.assertEqual(config.analysis_type, AnalysisType.OPERATING_POINT)

    def test_get_supported_analyses(self):
        """Test getting supported analysis types."""
        runner = SpiceRunner()
        analyses = runner.get_supported_analyses()
        self.assertIn(AnalysisType.OPERATING_POINT, analyses)
        self.assertIn(AnalysisType.TRANSIENT, analyses)
        self.assertIn(AnalysisType.AC_ANALYSIS, analyses)
        self.assertIn(AnalysisType.DC_SWEEP, analyses)

    def test_prepare_netlist(self):
        """Test netlist preparation with analysis commands."""
        runner = SpiceRunner()
        netlist = """* Test Circuit
R1 N1 0 1K
.END"""
        config = SpiceRunner.create_op_config()

        prepared = runner._prepare_netlist(netlist, config, None)

        self.assertIn(".OP", prepared.replace(" ", "").upper())
        self.assertIn(".CONTROL", prepared.replace(" ", "").upper())
        self.assertIn("run", prepared.lower())
        self.assertIn(".ENDC", prepared.replace(" ", "").upper())

    def test_prepare_netlist_with_probes(self):
        """Test netlist preparation with specific probe nodes."""
        runner = SpiceRunner()
        netlist = """* Test Circuit
R1 N1 N2 1K
.END"""
        config = SpiceRunner.create_transient_config()

        prepared = runner._prepare_netlist(netlist, config, ["N1", "N2"])

        self.assertIn("v(N1)", prepared)
        self.assertIn("v(N2)", prepared)

    def test_run_simulation_no_ngspice(self):
        """Test that simulation raises error when ngspice not available."""
        runner = SpiceRunner()
        # Manually set ngspice as unavailable
        runner._ngspice_available = False

        config = SpiceRunner.create_op_config()

        with self.assertRaises(NgspiceNotFoundError):
            runner.run_simulation("* test", config)


class TestAnalysisType(unittest.TestCase):
    """Tests for AnalysisType enum."""

    def test_enum_values(self):
        """Test that enum values are correct."""
        self.assertEqual(AnalysisType.OPERATING_POINT.value, "op")
        self.assertEqual(AnalysisType.DC_SWEEP.value, "dc")
        self.assertEqual(AnalysisType.AC_ANALYSIS.value, "ac")
        self.assertEqual(AnalysisType.TRANSIENT.value, "tran")


class TestCLIOutputParsing(unittest.TestCase):
    """Tests for CLI output parsing."""

    def test_parse_op_output(self):
        """Test parsing operating point output."""
        runner = SpiceRunner()
        result = SimulationResult(
            success=True,
            analysis_type=AnalysisType.OPERATING_POINT
        )

        output = """
v(n1) = 5.000000e+00
v(n2) = 2.500000e+00
i(v1) = -1.000000e-03
"""
        config = SpiceRunner.create_op_config()
        runner._parse_cli_output(result, output, config)

        self.assertIn("n1", result.operating_point)
        self.assertAlmostEqual(result.operating_point["n1"], 5.0)
        self.assertIn("n2", result.operating_point)
        self.assertAlmostEqual(result.operating_point["n2"], 2.5)

    def test_parse_current_output(self):
        """Test parsing current values from output."""
        runner = SpiceRunner()
        result = SimulationResult(
            success=True,
            analysis_type=AnalysisType.TRANSIENT
        )

        output = """
i(v1) = -0.001
i(r1) = 0.002
"""
        config = SpiceRunner.create_transient_config()
        runner._parse_cli_output(result, output, config)

        self.assertIn("v1", result.branch_currents)
        self.assertIn("r1", result.branch_currents)


if __name__ == "__main__":
    unittest.main()
