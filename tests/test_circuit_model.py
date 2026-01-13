import unittest
from core.pin import Pin, PinDirection
from core.net import Net
from core.component import Component


class TestCircuitModel(unittest.TestCase):
    def setUp(self):
        """
        This runs before every test method.
        We'll set up a small circuit:
          - R1 between NET1 and NET2
          - C1 between NET2 and GND
          - NET1, NET2, GND
        """
        # Nets
        self.net1 = Net("NET1")
        self.net2 = Net("NET2")
        self.gnd = Net("GND")

        # Components
        # Resistor R1 between NET1 and NET2
        r1_p1 = Pin("1", PinDirection.BIDIRECTIONAL)
        r1_p2 = Pin("2", PinDirection.BIDIRECTIONAL)
        self.r1 = Component("R1", pins=[r1_p1, r1_p2], parameters={"resistance": "1kΩ"})
        self.net1.connect(r1_p1)
        self.net2.connect(r1_p2)

        # Capacitor C1 between NET2 and GND
        c1_p1 = Pin("1", PinDirection.BIDIRECTIONAL)
        c1_p2 = Pin("2", PinDirection.BIDIRECTIONAL)
        self.c1 = Component("C1", pins=[c1_p1, c1_p2], parameters={"capacitance": "10uF"})
        self.net2.connect(c1_p1)
        self.gnd.connect(c1_p2)

        # Store all components and nets for convenience
        self.components = [self.r1, self.c1]
        self.nets = [self.net1, self.net2, self.gnd]

    def test_pin_net_connections(self):
        """Verify all pins are connected to the correct nets"""
        # R1 pins
        self.assertEqual(self.r1.pins[0].net, self.net1)
        self.assertEqual(self.r1.pins[1].net, self.net2)
        # C1 pins
        self.assertEqual(self.c1.pins[0].net, self.net2)
        self.assertEqual(self.c1.pins[1].net, self.gnd)

    def test_net_pins_list(self):
        """Verify nets contain the correct pins"""
        self.assertEqual(len(self.net1.pins), 1)
        self.assertIn(self.r1.pins[0], self.net1.pins)

        self.assertEqual(len(self.net2.pins), 2)
        self.assertIn(self.r1.pins[1], self.net2.pins)
        self.assertIn(self.c1.pins[0], self.net2.pins)

        self.assertEqual(len(self.gnd.pins), 1)
        self.assertIn(self.c1.pins[1], self.gnd.pins)

    def test_component_parameters(self):
        """Verify component parameters are correctly stored"""
        self.assertEqual(self.r1.parameters["resistance"], "1kΩ")
        self.assertEqual(self.c1.parameters["capacitance"], "10uF")

    def test_all_components_registered(self):
        """Verify all components are in the components list"""
        self.assertIn(self.r1, self.components)
        self.assertIn(self.c1, self.components)


if __name__ == "__main__":
    unittest.main()
