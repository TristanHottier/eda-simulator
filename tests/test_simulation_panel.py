# tests/test_simulation_panel.py
"""
Unit tests for Simulation Panel.
"""

import unittest
import sys

# Check if we can run GUI tests
try:
    from PySide6.QtWidgets import QApplication
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False


@unittest.skipUnless(GUI_AVAILABLE, "PySide6 not available")
class TestSimulationPanel(unittest. TestCase):
    """Tests for SimulationPanel widget."""

    @classmethod
    def setUpClass(cls):
        """Create QApplication for tests."""
        if not QApplication. instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def test_import(self):
        """Test that SimulationPanel can be imported."""
        from app.simulation_panel import SimulationPanel
        self.assertTrue(True)

    def test_parse_time_value(self):
        """Test time value parsing."""
        from app.simulation_panel import SimulationPanel
        from unittest.mock import MagicMock

        # Create panel with mock schematic view
        mock_view = MagicMock()
        panel = SimulationPanel(mock_view)

        # Test various time formats
        self.assertAlmostEqual(panel._parse_time_value("1m"), 1e-3)
        self.assertAlmostEqual(panel._parse_time_value("100u"), 100e-6)
        self.assertAlmostEqual(panel._parse_time_value("10n"), 10e-9)
        self.assertAlmostEqual(panel._parse_time_value("1p"), 1e-12)
        self.assertAlmostEqual(panel._parse_time_value("0.001"), 0.001)
        self.assertAlmostEqual(panel._parse_time_value("1s"), 1.0)

    def test_parse_time_value_invalid(self):
        """Test that invalid time values raise ValueError."""
        from app.simulation_panel import SimulationPanel
        from unittest.mock import MagicMock

        mock_view = MagicMock()
        panel = SimulationPanel(mock_view)

        with self.assertRaises(ValueError):
            panel._parse_time_value("invalid")

    def test_analysis_combo_items(self):
        """Test that analysis combo has correct items."""
        from app.simulation_panel import SimulationPanel
        from simulation.spice_runner import AnalysisType
        from unittest.mock import MagicMock

        mock_view = MagicMock()
        panel = SimulationPanel(mock_view)

        # Check that all analysis types are present
        items = []
        for i in range(panel._analysis_combo.count()):
            items.append(panel._analysis_combo.itemData(i))

        self.assertIn(AnalysisType.OPERATING_POINT, items)
        self.assertIn(AnalysisType.TRANSIENT, items)
        self.assertIn(AnalysisType.AC_ANALYSIS, items)
        self.assertIn(AnalysisType.DC_SWEEP, items)

    def test_parameter_groups_visibility(self):
        """Test that parameter groups show/hide based on analysis type."""
        from app.simulation_panel import SimulationPanel
        from simulation.spice_runner import AnalysisType
        from unittest.mock import MagicMock

        mock_view = MagicMock()
        panel = SimulationPanel(mock_view)

        # Use isHidden() instead of isVisible() for widgets not shown on screen
        # isVisible() returns False if any ancestor is not visible
        # isHidden() returns the widget's own hidden state

        # Operating Point (index 0) - no params visible
        panel._analysis_combo. setCurrentIndex(0)
        panel._on_analysis_changed(0)
        self.assertTrue(panel._transient_group.isHidden())
        self.assertTrue(panel._ac_group.isHidden())
        self.assertTrue(panel._dc_group.isHidden())

        # Transient (index 1) - transient params visible
        panel._analysis_combo.setCurrentIndex(1)
        panel._on_analysis_changed(1)
        self.assertFalse(panel._transient_group. isHidden())
        self.assertTrue(panel._ac_group.isHidden())
        self.assertTrue(panel._dc_group.isHidden())

        # AC (index 2) - AC params visible
        panel._analysis_combo.setCurrentIndex(2)
        panel._on_analysis_changed(2)
        self.assertTrue(panel._transient_group.isHidden())
        self.assertFalse(panel._ac_group.isHidden())
        self.assertTrue(panel._dc_group.isHidden())

        # DC Sweep (index 3) - DC params visible
        panel._analysis_combo.setCurrentIndex(3)
        panel._on_analysis_changed(3)
        self.assertTrue(panel._transient_group.isHidden())
        self.assertTrue(panel._ac_group.isHidden())
        self.assertFalse(panel._dc_group.isHidden())

    def test_build_op_config(self):
        """Test building operating point config."""
        from app.simulation_panel import SimulationPanel
        from simulation.spice_runner import AnalysisType
        from unittest.mock import MagicMock

        mock_view = MagicMock()
        panel = SimulationPanel(mock_view)

        panel._analysis_combo. setCurrentIndex(0)  # Operating Point
        config = panel._build_analysis_config()

        self.assertEqual(config. analysis_type, AnalysisType. OPERATING_POINT)

    def test_build_transient_config(self):
        """Test building transient config."""
        from app. simulation_panel import SimulationPanel
        from simulation.spice_runner import AnalysisType
        from unittest.mock import MagicMock

        mock_view = MagicMock()
        panel = SimulationPanel(mock_view)

        panel._analysis_combo.setCurrentIndex(1)  # Transient
        panel._tran_step. setText("1u")
        panel._tran_stop.setText("10m")

        config = panel._build_analysis_config()

        self.assertEqual(config.analysis_type, AnalysisType. TRANSIENT)
        self.assertAlmostEqual(config. step_time, 1e-6)
        self.assertAlmostEqual(config.stop_time, 10e-3)


@unittest.skipUnless(GUI_AVAILABLE, "PySide6 not available")
class TestSimulationWorker(unittest. TestCase):
    """Tests for SimulationWorker."""

    @classmethod
    def setUpClass(cls):
        """Create QApplication for tests."""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def test_worker_creation(self):
        """Test worker can be created."""
        from app. simulation_panel import SimulationWorker
        from simulation.spice_runner import SpiceRunner

        config = SpiceRunner.create_op_config()
        worker = SimulationWorker("* test netlist", config)

        self.assertIsNotNone(worker)


if __name__ == "__main__":
    unittest. main()
