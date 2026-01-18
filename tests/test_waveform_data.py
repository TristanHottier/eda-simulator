# tests/test_waveform_data.py
"""
Unit tests for Waveform Data Structures.
"""

import unittest
import math
from simulation.waveform_data import (
    Waveform,
    WaveformType,
    WaveformPoint,
    WaveformGroup,
    AxisType,
    OperatingPointData,
    SimulationData,
    get_waveform_color,
    WAVEFORM_COLORS
)


class TestWaveformPoint(unittest.TestCase):
    """Tests for WaveformPoint."""

    def test_creation(self):
        """Test point creation."""
        point = WaveformPoint(1.0, 2.5)
        self.assertEqual(point.x, 1.0)
        self.assertEqual(point.y, 2.5)

    def test_iteration(self):
        """Test that point is iterable."""
        point = WaveformPoint(1.0, 2.5)
        x, y = point
        self.assertEqual(x, 1.0)
        self.assertEqual(y, 2.5)


class TestWaveform(unittest.TestCase):
    """Tests for Waveform."""

    def test_creation(self):
        """Test waveform creation."""
        wf = Waveform(
            name="V(N1)",
            waveform_type=WaveformType.VOLTAGE,
            unit="V",
            x_data=[0, 1, 2, 3],
            y_data=[0, 1, 0, -1]
        )
        self.assertEqual(wf.name, "V(N1)")
        self.assertEqual(len(wf), 4)

    def test_length_mismatch_raises(self):
        """Test that mismatched data lengths raise an error."""
        with self.assertRaises(ValueError):
            Waveform(
                name="test",
                waveform_type=WaveformType.VOLTAGE,
                unit="V",
                x_data=[0, 1, 2],
                y_data=[0, 1]  # Different length
            )

    def test_min_max(self):
        """Test min/max properties."""
        wf = Waveform(
            name="test",
            waveform_type=WaveformType.VOLTAGE,
            unit="V",
            x_data=[0, 1, 2, 3],
            y_data=[-2, 1, 3, 0]
        )
        self.assertEqual(wf.x_min, 0)
        self.assertEqual(wf.x_max, 3)
        self.assertEqual(wf.y_min, -2)
        self.assertEqual(wf.y_max, 3)

    def test_peak_to_peak(self):
        """Test peak-to-peak calculation."""
        wf = Waveform(
            name="test",
            waveform_type=WaveformType.VOLTAGE,
            unit="V",
            x_data=[0, 1, 2, 3],
            y_data=[-2, 1, 3, 0]
        )
        self.assertEqual(wf.y_peak_to_peak, 5)  # 3 - (-2)

    def test_average(self):
        """Test average calculation."""
        wf = Waveform(
            name="test",
            waveform_type=WaveformType.VOLTAGE,
            unit="V",
            x_data=[0, 1, 2, 3],
            y_data=[1, 2, 3, 4]
        )
        self.assertEqual(wf.y_average, 2.5)

    def test_rms(self):
        """Test RMS calculation."""
        wf = Waveform(
            name="test",
            waveform_type=WaveformType.VOLTAGE,
            unit="V",
            x_data=[0, 1, 2],
            y_data=[1, 1, 1]
        )
        self.assertEqual(wf.y_rms, 1.0)

    def test_get_value_at_x_exact(self):
        """Test getting value at exact X position."""
        wf = Waveform(
            name="test",
            waveform_type=WaveformType.VOLTAGE,
            unit="V",
            x_data=[0, 1, 2],
            y_data=[0, 10, 20]
        )
        self.assertEqual(wf.get_value_at_x(1), 10)

    def test_get_value_at_x_interpolated(self):
        """Test getting interpolated value."""
        wf = Waveform(
            name="test",
            waveform_type=WaveformType.VOLTAGE,
            unit="V",
            x_data=[0, 2],
            y_data=[0, 10]
        )
        self.assertEqual(wf.get_value_at_x(1), 5)  # Midpoint

    def test_get_slice(self):
        """Test getting a slice of the waveform."""
        wf = Waveform(
            name="test",
            waveform_type=WaveformType.VOLTAGE,
            unit="V",
            x_data=[0, 1, 2, 3, 4, 5],
            y_data=[0, 1, 2, 3, 4, 5]
        )
        sliced = wf.get_slice(1.5, 3.5)
        self.assertEqual(len(sliced), 2)
        self.assertEqual(sliced.x_data, [2, 3])

    def test_iteration(self):
        """Test iterating over waveform points."""
        wf = Waveform(
            name="test",
            waveform_type=WaveformType.VOLTAGE,
            unit="V",
            x_data=[0, 1, 2],
            y_data=[0, 10, 20]
        )
        points = list(wf)
        self.assertEqual(len(points), 3)
        self.assertEqual(points[1].x, 1)
        self.assertEqual(points[1].y, 10)

    def test_to_dict_from_dict(self):
        """Test serialization round-trip."""
        wf = Waveform(
            name="V(N1)",
            waveform_type=WaveformType.VOLTAGE,
            unit="V",
            x_data=[0, 1, 2],
            y_data=[0, 5, 10],
            color="#FF0000"
        )
        data = wf.to_dict()
        restored = Waveform.from_dict(data)

        self.assertEqual(restored.name, wf.name)
        self.assertEqual(restored.x_data, wf.x_data)
        self.assertEqual(restored.y_data, wf.y_data)
        self.assertEqual(restored.color, wf.color)

    def test_empty_waveform(self):
        """Test empty waveform properties."""
        wf = Waveform(
            name="empty",
            waveform_type=WaveformType.VOLTAGE,
            unit="V",
            x_data=[],
            y_data=[]
        )
        self.assertTrue(wf.is_empty)
        self.assertIsNone(wf.x_min)
        self.assertIsNone(wf.y_average)


class TestWaveformGroup(unittest.TestCase):
    """Tests for WaveformGroup."""

    def test_creation(self):
        """Test group creation."""
        group = WaveformGroup(
            name="Transient",
            x_type=AxisType.TIME,
            x_unit="s",
            x_data=[0, 1, 2, 3]
        )
        self.assertEqual(group.name, "Transient")
        self.assertEqual(len(group), 0)

    def test_add_waveform(self):
        """Test adding waveform to group."""
        group = WaveformGroup(
            name="Transient",
            x_type=AxisType.TIME,
            x_unit="s",
            x_data=[0, 1, 2]
        )
        wf = group.add_waveform("V(N1)", [0, 5, 10])

        self.assertEqual(len(group), 1)
        self.assertIn("V(N1)", group)
        self.assertEqual(wf.name, "V(N1)")

    def test_add_waveform_length_mismatch(self):
        """Test that adding mismatched waveform raises error."""
        group = WaveformGroup(
            name="Transient",
            x_type=AxisType.TIME,
            x_unit="s",
            x_data=[0, 1, 2]
        )
        with self.assertRaises(ValueError):
            group.add_waveform("V(N1)", [0, 5])  # Wrong length

    def test_get_waveform(self):
        """Test getting waveform by name."""
        group = WaveformGroup(
            name="Transient",
            x_type=AxisType.TIME,
            x_unit="s",
            x_data=[0, 1, 2]
        )
        group.add_waveform("V(N1)", [0, 5, 10])

        wf = group.get_waveform("V(N1)")
        self.assertIsNotNone(wf)
        self.assertEqual(wf.name, "V(N1)")

        self.assertIsNone(group.get_waveform("nonexistent"))

    def test_remove_waveform(self):
        """Test removing waveform."""
        group = WaveformGroup(
            name="Transient",
            x_type=AxisType.TIME,
            x_unit="s",
            x_data=[0, 1, 2]
        )
        group.add_waveform("V(N1)", [0, 5, 10])

        self.assertTrue(group.remove_waveform("V(N1)"))
        self.assertEqual(len(group), 0)
        self.assertFalse(group.remove_waveform("nonexistent"))

    def test_visible_waveforms(self):
        """Test filtering visible waveforms."""
        group = WaveformGroup(
            name="Transient",
            x_type=AxisType.TIME,
            x_unit="s",
            x_data=[0, 1, 2]
        )
        wf1 = group.add_waveform("V(N1)", [0, 5, 10])
        wf2 = group.add_waveform("V(N2)", [0, 3, 6])
        wf2.visible = False

        visible = group.get_visible_waveforms()
        self.assertEqual(len(visible), 1)
        self.assertEqual(visible[0].name, "V(N1)")


class TestOperatingPointData(unittest.TestCase):
    """Tests for OperatingPointData."""

    def test_creation(self):
        """Test creation with data."""
        op = OperatingPointData(
            node_voltages={"N1": 5.0, "N2": 2.5},
            branch_currents={"V1": 0.001}
        )
        self.assertEqual(op.get_voltage("N1"), 5.0)
        self.assertEqual(op.get_current("V1"), 0.001)

    def test_get_nonexistent(self):
        """Test getting nonexistent values."""
        op = OperatingPointData()
        self.assertIsNone(op.get_voltage("N1"))
        self.assertIsNone(op.get_current("R1"))

    def test_get_power(self):
        """Test power calculation."""
        op = OperatingPointData(
            node_voltages={"N1": 5.0},
            branch_currents={"R1": 0.01}
        )
        power = op.get_power("N1", "R1")
        self.assertEqual(power, 0.05)  # 5V * 0.01A

    def test_get_all_nodes(self):
        """Test getting all node names."""
        op = OperatingPointData(
            node_voltages={"N1": 5.0, "N2": 2.5, "N3": 0}
        )
        nodes = op.get_all_nodes()
        self.assertEqual(set(nodes), {"N1", "N2", "N3"})

    def test_serialization(self):
        """Test to_dict and from_dict."""
        op = OperatingPointData(
            node_voltages={"N1": 5.0},
            branch_currents={"V1": 0.001}
        )
        data = op.to_dict()
        restored = OperatingPointData.from_dict(data)

        self.assertEqual(restored.get_voltage("N1"), 5.0)
        self.assertEqual(restored.get_current("V1"), 0.001)


class TestSimulationData(unittest.TestCase):
    """Tests for SimulationData."""

    def test_empty_creation(self):
        """Test empty simulation data."""
        sim = SimulationData(title="Test")
        self.assertEqual(sim.title, "Test")
        self.assertFalse(sim.has_operating_point())
        self.assertFalse(sim.has_transient())

    def test_has_operating_point(self):
        """Test has_operating_point check."""
        sim = SimulationData()
        sim.operating_point = OperatingPointData(
            node_voltages={"N1": 5.0}
        )
        self.assertTrue(sim.has_operating_point())

    def test_has_transient(self):
        """Test has_transient check."""
        sim = SimulationData()
        sim.transient = WaveformGroup(
            name="Transient",
            x_type=AxisType.TIME,
            x_unit="s",
            x_data=[0, 1]
        )
        sim.transient.add_waveform("V(N1)", [0, 5])
        self.assertTrue(sim.has_transient())

    def test_get_available_analyses(self):
        """Test getting available analysis types."""
        sim = SimulationData()
        sim.operating_point = OperatingPointData(node_voltages={"N1": 5.0})
        sim.transient = WaveformGroup(
            name="Transient",
            x_type=AxisType.TIME,
            x_unit="s",
            x_data=[0, 1]
        )
        sim.transient.add_waveform("V(N1)", [0, 5])

        analyses = sim.get_available_analyses()
        self.assertIn("operating_point", analyses)
        self.assertIn("transient", analyses)
        self.assertNotIn("ac_analysis", analyses)

    def test_clear(self):
        """Test clearing simulation data."""
        sim = SimulationData()
        sim.operating_point = OperatingPointData(node_voltages={"N1": 5.0})
        sim.clear()

        self.assertFalse(sim.has_operating_point())


class TestWaveformColors(unittest.TestCase):
    """Tests for waveform color utilities."""

    def test_get_color(self):
        """Test getting colors by index."""
        color0 = get_waveform_color(0)
        color1 = get_waveform_color(1)

        self.assertIsInstance(color0, str)
        self.assertTrue(color0.startswith("#"))
        self.assertNotEqual(color0, color1)

    def test_color_wrapping(self):
        """Test that colors wrap around."""
        num_colors = len(WAVEFORM_COLORS)
        color0 = get_waveform_color(0)
        color_wrapped = get_waveform_color(num_colors)

        self.assertEqual(color0, color_wrapped)


if __name__ == "__main__":
    unittest.main()
