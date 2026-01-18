# tests/test_waveform_viewer.py
"""
Unit tests for Waveform Viewer.
"""

import unittest
import sys

# Check if we can run GUI tests
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt

    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

from simulation.waveform_data import (
    Waveform, WaveformType, WaveformGroup, AxisType,
    SimulationData, OperatingPointData, get_waveform_color
)


@unittest.skipUnless(GUI_AVAILABLE, "PySide6 not available")
class TestWaveformViewer(unittest.TestCase):
    """Tests for WaveformViewer widget."""

    @classmethod
    def setUpClass(cls):
        """Create QApplication for tests."""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def test_import(self):
        """Test that WaveformViewer can be imported."""
        from ui.waveform_viewer import WaveformViewer
        self.assertTrue(True)

    def test_creation(self):
        """Test WaveformViewer creation."""
        from ui.waveform_viewer import WaveformViewer
        viewer = WaveformViewer()
        self.assertIsNotNone(viewer)

    def test_set_simulation_data(self):
        """Test setting simulation data."""
        from ui.waveform_viewer import WaveformViewer

        viewer = WaveformViewer()

        # Create test data
        sim_data = SimulationData(title="Test")
        sim_data.operating_point = OperatingPointData(
            node_voltages={"N1": 5.0, "N2": 2.5}
        )

        viewer.set_simulation_data(sim_data)
        # Should not raise
        self.assertTrue(True)

    def test_clear(self):
        """Test clearing the viewer."""
        from ui.waveform_viewer import WaveformViewer

        viewer = WaveformViewer()
        viewer.clear()
        # Should not raise
        self.assertTrue(True)

    def test_dark_mode(self):
        """Test dark mode toggle."""
        from ui.waveform_viewer import WaveformViewer

        viewer = WaveformViewer()
        viewer.set_dark_mode(True)
        viewer.set_dark_mode(False)
        # Should not raise
        self.assertTrue(True)


@unittest.skipUnless(GUI_AVAILABLE, "PySide6 not available")
class TestWaveformPlot(unittest.TestCase):
    """Tests for WaveformPlot widget."""

    @classmethod
    def setUpClass(cls):
        """Create QApplication for tests."""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def test_creation(self):
        """Test WaveformPlot creation."""
        from ui.waveform_viewer import WaveformPlot
        plot = WaveformPlot(title="Test", x_label="X", y_label="Y")
        self.assertIsNotNone(plot)

    def test_add_waveform(self):
        """Test adding a waveform."""
        from ui.waveform_viewer import WaveformPlot, PYQTGRAPH_AVAILABLE

        plot = WaveformPlot()
        waveform = Waveform(
            name="V(N1)",
            waveform_type=WaveformType.VOLTAGE,
            unit="V",
            x_data=[0, 1, 2, 3],
            y_data=[0, 1, 0, -1]
        )

        result = plot.add_waveform(waveform)

        if PYQTGRAPH_AVAILABLE:
            self.assertTrue(result)
            self.assertIn("V(N1)", plot.get_waveform_names())
        else:
            self.assertFalse(result)

    def test_remove_waveform(self):
        """Test removing a waveform."""
        from ui.waveform_viewer import WaveformPlot, PYQTGRAPH_AVAILABLE

        if not PYQTGRAPH_AVAILABLE:
            self.skipTest("PyQtGraph not available")

        plot = WaveformPlot()
        waveform = Waveform(
            name="V(N1)",
            waveform_type=WaveformType.VOLTAGE,
            unit="V",
            x_data=[0, 1, 2],
            y_data=[0, 5, 10]
        )

        plot.add_waveform(waveform)
        result = plot.remove_waveform("V(N1)")

        self.assertTrue(result)
        self.assertNotIn("V(N1)", plot.get_waveform_names())

    def test_clear_all(self):
        """Test clearing all waveforms."""
        from ui.waveform_viewer import WaveformPlot, PYQTGRAPH_AVAILABLE

        if not PYQTGRAPH_AVAILABLE:
            self.skipTest("PyQtGraph not available")

        plot = WaveformPlot()
        waveform = Waveform(
            name="V(N1)",
            waveform_type=WaveformType.VOLTAGE,
            unit="V",
            x_data=[0, 1, 2],
            y_data=[0, 5, 10]
        )

        plot.add_waveform(waveform)
        plot.clear_all()

        self.assertEqual(len(plot.get_waveform_names()), 0)


@unittest.skipUnless(GUI_AVAILABLE, "PySide6 not available")
class TestOperatingPointPanel(unittest.TestCase):
    """Tests for OperatingPointPanel widget."""

    @classmethod
    def setUpClass(cls):
        """Create QApplication for tests."""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def test_creation(self):
        """Test OperatingPointPanel creation."""
        from ui.waveform_viewer import OperatingPointPanel
        panel = OperatingPointPanel()
        self.assertIsNotNone(panel)

    def test_set_data(self):
        """Test setting operating point data."""
        from ui.waveform_viewer import OperatingPointPanel

        panel = OperatingPointPanel()
        op_data = OperatingPointData(
            node_voltages={"N1": 5.0, "N2": 2.5},
            branch_currents={"V1": 0.001}
        )

        panel.set_data(op_data)
        # Should not raise
        self.assertTrue(True)

    def test_clear(self):
        """Test clearing the panel."""
        from ui.waveform_viewer import OperatingPointPanel

        panel = OperatingPointPanel()
        panel.clear()
        # Should not raise
        self.assertTrue(True)


@unittest.skipUnless(GUI_AVAILABLE, "PySide6 not available")
class TestCursorReadout(unittest.TestCase):
    """Tests for CursorReadout widget."""

    @classmethod
    def setUpClass(cls):
        """Create QApplication for tests."""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def test_creation(self):
        """Test CursorReadout creation."""
        from ui.waveform_viewer import CursorReadout
        readout = CursorReadout()
        self.assertIsNotNone(readout)

    def test_update_position(self):
        """Test updating cursor position."""
        from ui.waveform_viewer import CursorReadout

        readout = CursorReadout()
        readout.update_position(1.5e-6, 3.3)
        # Should not raise
        self.assertTrue(True)

    def test_format_values(self):
        """Test value formatting at different scales."""
        from ui.waveform_viewer import CursorReadout

        readout = CursorReadout()

        # Test various magnitudes
        readout.update_position(1e-12, 1e-12)  # pico
        readout.update_position(1e-9, 1e-9)  # nano
        readout.update_position(1e-6, 1e-6)  # micro
        readout.update_position(1e-3, 1e-3)  # milli
        readout.update_position(1, 1)  # base
        readout.update_position(1e3, 1e3)  # kilo
        readout.update_position(1e6, 1e6)  # mega

        # Should not raise
        self.assertTrue(True)


class TestWaveformColors(unittest.TestCase):
    """Tests for waveform color utilities."""

    def test_get_color_returns_string(self):
        """Test that get_waveform_color returns a hex string."""
        color = get_waveform_color(0)
        self.assertIsInstance(color, str)
        self.assertTrue(color.startswith("#"))

    def test_colors_are_unique(self):
        """Test that first 10 colors are unique."""
        from simulation.waveform_data import WAVEFORM_COLORS

        colors = [get_waveform_color(i) for i in range(len(WAVEFORM_COLORS))]
        self.assertEqual(len(colors), len(set(colors)))


if __name__ == "__main__":
    unittest.main()
