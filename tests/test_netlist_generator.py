# tests/test_netlist_generator.py
"""
Unit tests for the Netlist Generator.
"""

import unittest
from simulation.netlist_generator import (
    NetlistGenerator,
    NetlistComponent,
    MissingGroundError,
    FloatingNodeError
)


class TestNetlistComponent(unittest.TestCase):
    """Tests for NetlistComponent SPICE output formatting."""

    def test_resistor_to_spice(self):
        """Test resistor SPICE format."""
        comp = NetlistComponent(
            ref="1",
            comp_type="resistor",
            nodes=["N1", "N2"],
            parameters={"resistance": 1000}
        )
        result = comp.to_spice()
        self.assertEqual(result, "R1 N1 N2 1.0K")

    def test_resistor_megohm(self):
        """Test resistor with megohm value."""
        comp = NetlistComponent(
            ref="2",
            comp_type="resistor",
            nodes=["N1", "0"],
            parameters={"resistance": 2200000}
        )
        result = comp.to_spice()
        self.assertEqual(result, "R2 N1 0 2.2MEG")

    def test_capacitor_to_spice(self):
        """Test capacitor SPICE format."""
        comp = NetlistComponent(
            ref="1",
            comp_type="capacitor",
            nodes=["N1", "0"],
            parameters={"capacitance": 100}  # 100nF
        )
        result = comp.to_spice()
        self.assertIn("C1 N1 0", result)
        self.assertIn("N", result)  # nanofarad

    def test_inductor_to_spice(self):
        """Test inductor SPICE format."""
        comp = NetlistComponent(
            ref="1",
            comp_type="inductor",
            nodes=["N1", "N2"],
            parameters={"inductance":  10}  # 10mH
        )
        result = comp.to_spice()
        self.assertIn("L1 N1 N2", result)

    def test_dc_voltage_source_to_spice(self):
        """Test DC voltage source SPICE format."""
        comp = NetlistComponent(
            ref="1",
            comp_type="dc_voltage_source",
            nodes=["N1", "0"],
            parameters={"voltage": 12.0}
        )
        result = comp.to_spice()
        self.assertEqual(result, "V1 N1 0 DC 12.0")

    def test_ac_voltage_source_to_spice(self):
        """Test AC voltage source SPICE format."""
        comp = NetlistComponent(
            ref="1",
            comp_type="ac_voltage_source",
            nodes=["N1", "0"],
            parameters={"voltage": 5.0, "frequency": 1000}
        )
        result = comp.to_spice()
        self.assertIn("V1 N1 0 AC", result)
        self.assertIn("SIN", result)

    def test_dc_current_source_to_spice(self):
        """Test DC current source SPICE format."""
        comp = NetlistComponent(
            ref="1",
            comp_type="dc_current_source",
            nodes=["N1", "0"],
            parameters={"current": 0.01}
        )
        result = comp.to_spice()
        self.assertEqual(result, "I1 N1 0 DC 0.01")

    def test_led_to_spice(self):
        """Test LED SPICE format (diode model)."""
        comp = NetlistComponent(
            ref="1",
            comp_type="led",
            nodes=["N1", "N2"],
            parameters={"voltage_drop": 2.0}
        )
        result = comp.to_spice()
        self.assertIn("D1", result)
        self.assertIn("LED_MODEL", result)

    def test_ground_returns_empty(self):
        """Test that ground component returns empty string."""
        comp = NetlistComponent(
            ref="1",
            comp_type="ground",
            nodes=["0"],
            parameters={}
        )
        result = comp.to_spice()
        self.assertEqual(result, "")


class TestNetlistGenerator(unittest.TestCase):
    """Tests for NetlistGenerator."""

    def test_generator_initialization(self):
        """Test generator initializes correctly."""
        gen = NetlistGenerator()
        self.assertEqual(len(gen.components), 0)
        self.assertEqual(len(gen.node_map), 0)
        self.assertFalse(gen.has_ground)

    def test_format_netlist_basic(self):
        """Test basic netlist formatting."""
        gen = NetlistGenerator()
        gen.has_ground = True
        gen.components = [
            NetlistComponent(
                ref="1",
                comp_type="resistor",
                nodes=["N1", "0"],
                parameters={"resistance": 1000}
            )
        ]

        result = gen._format_netlist()

        self.assertIn("EDA Simulator Generated Netlist", result)
        self.assertIn("R1 N1 0", result)
        self.assertIn(".END", result)

    def test_missing_ground_raises_error(self):
        """Test that missing ground raises MissingGroundError."""
        gen = NetlistGenerator()
        gen.has_ground = False
        gen.components = []

        with self.assertRaises(MissingGroundError):
            gen._validate_circuit()

    def test_get_node_list(self):
        """Test getting list of all nodes."""
        gen = NetlistGenerator()
        gen.components = [
            NetlistComponent("1", "resistor", ["N1", "N2"], {}),
            NetlistComponent("2", "resistor", ["N2", "0"], {}),
        ]

        nodes = gen.get_node_list()

        self.assertIn("N1", nodes)
        self.assertIn("N2", nodes)
        self.assertIn("0", nodes)

    def test_get_component_count(self):
        """Test counting components by type."""
        gen = NetlistGenerator()
        gen.components = [
            NetlistComponent("1", "resistor", ["N1", "N2"], {}),
            NetlistComponent("2", "resistor", ["N2", "0"], {}),
            NetlistComponent("1", "capacitor", ["N1", "0"], {}),
        ]

        counts = gen.get_component_count()

        self.assertEqual(counts["resistor"], 2)
        self.assertEqual(counts["capacitor"], 1)

    def test_netlist_includes_models(self):
        """Test that netlist includes required SPICE models."""
        gen = NetlistGenerator()
        gen.has_ground = True
        gen.components = [
            NetlistComponent("1", "led", ["N1", "0"], {})
        ]

        result = gen._format_netlist()

        self.assertIn(".MODEL LED_MODEL", result)

    def test_warnings_included_as_comments(self):
        """Test that warnings are included as comments in netlist."""
        gen = NetlistGenerator()
        gen.has_ground = True
        gen.components = []
        gen.warnings = ["Test warning message"]

        result = gen._format_netlist()

        self.assertIn("* WARNING: Test warning message", result)


class TestResistanceFormatting(unittest.TestCase):
    """Tests for resistance value formatting."""

    def test_ohms(self):
        """Test formatting values in ohms."""
        comp = NetlistComponent("1", "resistor", ["A", "B"], {"resistance": 100})
        self.assertIn("100", comp.to_spice())

    def test_kilohms(self):
        """Test formatting values in kilohms."""
        comp = NetlistComponent("1", "resistor", ["A", "B"], {"resistance": 4700})
        self.assertIn("4.7K", comp.to_spice())

    def test_megohms(self):
        """Test formatting values in megohms."""
        comp = NetlistComponent("1", "resistor", ["A", "B"], {"resistance":  1000000})
        self.assertIn("1.0MEG", comp.to_spice())


if __name__ == "__main__":
    unittest.main()
