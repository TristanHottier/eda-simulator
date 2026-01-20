# simulation/netlist_generator.py
"""
Netlist Generator — Converts the schematic circuit model to SPICE netlist format.

This module traverses the schematic components and wire connections to produce
a valid SPICE netlist that can be executed by ngspice or PySpice.
"""

from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum


class NetlistError(Exception):
    """Base exception for netlist generation errors."""
    pass


class MissingGroundError(NetlistError):
    """Raised when the circuit has no ground reference."""
    pass


class FloatingNodeError(NetlistError):
    """Raised when a node has fewer than 2 connections."""

    def __init__(self, node_name: str):
        self.node_name = node_name
        super().__init__(f"Floating node detected: {node_name}")


class InvalidComponentError(NetlistError):
    """Raised when a component has invalid parameters."""

    def __init__(self, component_ref: str, message: str):
        self.component_ref = component_ref
        super().__init__(f"Invalid component {component_ref}: {message}")


@dataclass
class NetlistComponent:
    """Represents a component in the netlist."""
    ref: str
    comp_type: str
    nodes: List[str]  # Node names for each pin
    parameters: Dict[str, any]

    def to_spice(self) -> str:
        """Converts this component to a SPICE netlist line."""
        if self.comp_type == "resistor":
            # R<name> <node1> <node2> <value>
            value = self._format_resistance(self.parameters.get("resistance", 1000))
            return f"R{self.ref} {self.nodes[0]} {self.nodes[1]} {value}"

        elif self.comp_type == "capacitor":
            # C<name> <node1> <node2> <value>
            value = self._format_capacitance(self.parameters.get("capacitance", 1))
            return f"C{self.ref} {self.nodes[0]} {self.nodes[1]} {value}\n.IC V({self.nodes[0]})=0"

        elif self.comp_type == "inductor":
            # L<name> <node1> <node2> <value>
            value = self._format_inductance(self.parameters.get("inductance", 100))
            return f"L{self.ref} {self.nodes[0]} {self.nodes[1]} {value}"

        elif self.comp_type == "dc_voltage_source":
            # V<name> <node+> <node-> DC <value>
            value = self.parameters.get("voltage", 5.0)
            return f"V{self.ref} {self.nodes[0]} {self.nodes[1]} DC {value}"

        elif self.comp_type == "ac_voltage_source":
            # V<name> <node+> <node-> AC <amplitude> <frequency>
            voltage = self.parameters.get("voltage", 5.0)
            freq = self.parameters.get("frequency", 1000)
            return f"V{self.ref} {self.nodes[0]} {self.nodes[1]} AC {voltage} SIN(0 {voltage} {freq})"

        elif self.comp_type == "dc_current_source":
            # I<name> <node+> <node-> DC <value>
            value = self.parameters.get("current", 0.001)
            return f"I{self.ref} {self.nodes[0]} {self.nodes[1]} DC {value}"

        elif self.comp_type == "led":
            # Model LED as a diode with typical forward voltage
            # D<name> <anode> <cathode> <model>
            return f"D{self.ref} {self.nodes[0]} {self.nodes[1]} LED_MODEL"

        elif self.comp_type == "diode":
            # Check if a unique model name was assigned during _format_netlist
            if hasattr(self, "spice_model_name"):
                model_name = self.spice_model_name
            else:
                # Fallback (should ideally not be reached if _format_netlist runs first)
                diode_type = self.parameters.get("diode_type", "silicon")
                if diode_type == "zener":
                    model_name = "DZEN"
                elif diode_type == "schottky":
                    model_name = "DSCH"
                else:
                    model_name = "DSTD"
            return f"D{self.ref} {self.nodes[0]} {self.nodes[1]} {model_name}"

        elif self.comp_type == "ground":
            # Ground is handled separately (node 0)
            return ""

        else:
            # Generic/unknown component - skip with comment
            return f"* Unknown component:  {self.ref} ({self.comp_type})"

    def _format_resistance(self, value: float) -> str:
        """Formats resistance value with appropriate suffix."""
        if value >= 1e6:
            return f"{value / 1e6}MEG"
        elif value >= 1e3:
            return f"{value / 1e3}K"
        else:
            return str(value)

    def _format_capacitance(self, value: float) -> str:
        """Formats capacitance value (input assumed in nF) with appropriate suffix."""
        # Input is in nF, convert to F for SPICE
        value_f = value * 1e-9
        if value_f >= 1e-6:
            return f"{value_f * 1e6}U"
        elif value_f >= 1e-9:
            return f"{value_f * 1e9}N"
        elif value_f >= 1e-12:
            return f"{value_f * 1e12}P"
        else:
            return f"{value_f}"

    def _format_inductance(self, value: float) -> str:
        """Formats inductance value (input assumed in mH) with appropriate suffix."""
        # Input is in mH, convert to H for SPICE
        value_h = value * 1e-3
        if value_h >= 1:
            return f"{value_h}"
        elif value_h >= 1e-3:
            return f"{value_h * 1e3}M"
        elif value_h >= 1e-6:
            return f"{value_h * 1e6}U"
        else:
            return f"{value_h}"


class NetlistGenerator:
    """
    Generates SPICE netlists from schematic data.

    The generator traverses the schematic's components and wire connections
    to build a complete netlist suitable for simulation.
    """

    def __init__(self):
        self.components: List[NetlistComponent] = []
        self.node_map: Dict[Tuple[float, float], str] = {}  # Position -> node name
        self.node_counter = 1
        self.has_ground = False
        self.errors: List[NetlistError] = []
        self.warnings: List[str] = []

    def generate(self, schematic_view) -> str:
        """
        Generates a SPICE netlist from the schematic view.

        Args:
            schematic_view: The SchematicView instance containing the circuit.

        Returns:
            str: The complete SPICE netlist as a string.

        Raises:
            MissingGroundError: If no ground component is found.
            FloatingNodeError: If a node has insufficient connections.
        """
        self._reset()
        self._build_node_map(schematic_view)
        self._extract_components(schematic_view)
        self._validate_circuit()

        return self._format_netlist()

    def generate_from_data(
            self,
            components_data: List[Dict],
            wires_data: List[Dict],
            point_to_net: Dict[Tuple[float, float], int]
    ) -> str:
        """
        Generates a SPICE netlist from raw schematic data.

        This method allows generating netlists without requiring a full
        SchematicView instance, useful for testing or batch processing.

        Args:
            components_data: List of component dictionaries with position info.
            wires_data: List of wire segment dictionaries.
            point_to_net:  Mapping from positions to net IDs.

        Returns:
            str:  The complete SPICE netlist as a string.
        """
        self._reset()
        self._build_node_map_from_data(wires_data, point_to_net)
        self._extract_components_from_data(components_data)
        self._validate_circuit()

        return self._format_netlist()

    def _reset(self) -> None:
        """Resets the generator state for a new netlist."""
        self.components = []
        self.node_map = {}
        self.node_counter = 1
        self.has_ground = False
        self.errors = []
        self.warnings = []

    def _build_node_map(self, schematic_view) -> None:
        """Builds a mapping from wire endpoints to node names."""
        from ui.component_item import ComponentItem
        from ui.wire_segment_item import WireSegmentItem

        # First pass: identify ground nodes
        for item in schematic_view.scene().items():
            if isinstance(item, ComponentItem):
                if item.model.type == "ground":
                    self.has_ground = True
                    # Get the pin position in scene coordinates
                    for pin_item in item.pin_items:
                        pin_pos = pin_item.scene_connection_point()
                        pos_key = (round(pin_pos.x()), round(pin_pos.y()))
                        self.node_map[pos_key] = "0"  # Ground is always node 0

        # Second pass: assign node names based on net IDs
        for pos, net_id in schematic_view.point_to_net.items():
            pos_key = (round(pos[0]), round(pos[1]))
            if pos_key not in self.node_map:
                # Check if this net connects to ground
                if self._net_connects_to_ground(pos_key, schematic_view):
                    self.node_map[pos_key] = "0"
                else:
                    self.node_map[pos_key] = f"N{net_id}"

    def _net_connects_to_ground(self, pos: Tuple[float, float], schematic_view) -> bool:
        """Checks if a position's net connects to a ground node."""
        net_id = schematic_view.point_to_net.get(pos)
        if net_id is None:
            return False

        # Check all points in the same net
        for other_pos, other_net_id in schematic_view.point_to_net.items():
            if other_net_id == net_id:
                other_key = (round(other_pos[0]), round(other_pos[1]))
                if self.node_map.get(other_key) == "0":
                    return True
        return False

    def _build_node_map_from_data(
            self,
            wires_data: List[Dict],
            point_to_net: Dict[Tuple[float, float], int]
    ) -> None:
        """Builds node map from raw wire data."""
        for pos, net_id in point_to_net.items():
            pos_key = (round(pos[0]), round(pos[1]))
            if pos_key not in self.node_map:
                self.node_map[pos_key] = f"N{net_id}"

    def _extract_components(self, schematic_view) -> None:
        """Extracts component data from the schematic view."""
        from ui.component_item import ComponentItem

        for item in schematic_view.scene().items():
            if isinstance(item, ComponentItem):
                component = self._create_netlist_component(item)
                if component:
                    self.components.append(component)

    def _extract_components_from_data(self, components_data: List[Dict]) -> None:
        """Extracts component data from raw component dictionaries."""
        for comp_data in components_data:
            # This simplified version assumes pin positions are included
            # In a full implementation, we'd calculate pin positions from component position
            ref = comp_data.get("ref", "")
            comp_type = comp_data.get("comp_type", "generic")
            parameters = comp_data.get("parameters", {})

            if comp_type == "ground":
                self.has_ground = True
                continue

            # Get node names for pins (simplified - uses component position)
            nodes = self._get_nodes_for_component_data(comp_data)

            component = NetlistComponent(
                ref=ref.lstrip("RCLVIGND"),  # Remove prefix for SPICE
                comp_type=comp_type,
                nodes=nodes,
                parameters=parameters
            )
            self.components.append(component)

    def _create_netlist_component(self, item) -> Optional[NetlistComponent]:
        """Creates a NetlistComponent from a ComponentItem."""
        model = item.model
        comp_type = model.type

        # Ground is handled specially (sets node 0)
        if comp_type == "ground":
            self.has_ground = True
            return None

        # Get node names for each pin
        nodes = []
        for pin_item in item.pin_items:
            pin_pos = pin_item.scene_connection_point()
            pos_key = (round(pin_pos.x()), round(pin_pos.y()))

            # Find the node name for this position
            node_name = self.node_map.get(pos_key)
            if node_name is None:
                # Pin is not connected to any wire - create a floating node
                node_name = f"NC_{self.node_counter}"
                self.node_counter += 1
                self.warnings.append(f"Pin {pin_item.pin_logic.name} of {model.ref} is not connected")

            nodes.append(node_name)

        # Strip the type prefix from ref for SPICE (e.g., "R1" -> "1")
        ref_stripped = model.ref.lstrip("RCLVIGND")
        if not ref_stripped:
            ref_stripped = model.ref

        return NetlistComponent(
            ref=ref_stripped,
            comp_type=comp_type,
            nodes=nodes,
            parameters=dict(model.parameters)
        )

    def _get_nodes_for_component_data(self, comp_data: Dict) -> List[str]:
        """Gets node names for a component from raw data."""
        # This is a simplified implementation
        # In practice, we'd need to calculate actual pin positions
        x = comp_data.get("x", 0)
        y = comp_data.get("y", 0)

        # Check nearby positions in node_map
        nodes = []
        for pos_key, node_name in self.node_map.items():
            # Simple proximity check (within component bounds)
            if abs(pos_key[0] - x) < 150 and abs(pos_key[1] - y) < 150:
                nodes.append(node_name)
                if len(nodes) >= 2:
                    break

        # Pad with unconnected nodes if needed
        while len(nodes) < 2:
            nodes.append(f"NC_{self.node_counter}")
            self.node_counter += 1

        return nodes

    def _validate_circuit(self) -> None:
        """Validates the circuit for common errors."""
        if not self.has_ground:
            raise MissingGroundError("Circuit must have a ground reference (node 0)")

        # Check for floating nodes (nodes with only one connection)
        node_connections: Dict[str, int] = {}
        for component in self.components:
            for node in component.nodes:
                if node.startswith("NC_"):
                    continue  # Skip unconnected markers
                node_connections[node] = node_connections.get(node, 0) + 1

        for node, count in node_connections.items():
            if count < 2 and node != "0":
                self.warnings.append(f"Node {node} has only {count} connection(s)")

    def _format_netlist(self) -> str:
        """Formats the complete SPICE netlist."""
        lines = []

        # Title
        lines.append("* EDA Simulator Generated Netlist")
        lines.append(f"* Components: {len(self.components)}")
        lines.append("")

        # --- Deduplicate Diode Models Pass ---
        diode_models = {}
        model_id_counter = {"silicon": 1, "schottky": 1, "zener": 1}
        led_models_used = set()

        for component in self.components:
            if component.comp_type == "diode":
                dtype = component.parameters.get("diode_type", "silicon")
                # Gather model params for uniqueness
                if dtype == "zener":
                    param_keys = ("IS", "N", "BV", "IBV")
                    params = (
                        dtype,
                        component.parameters.get("IS", 5e-14),
                        component.parameters.get("N", 1.0),
                        component.parameters.get("BV", 5.6),
                        component.parameters.get("IBV", 1e-3)
                    )
                elif dtype == "schottky":
                    param_keys = ("IS", "N", "TT")
                    params = (
                        dtype,
                        component.parameters.get("IS", 2e-14),
                        component.parameters.get("N", 1.05),
                        component.parameters.get("TT", 1e-9)
                    )
                else:  # "silicon"
                    param_keys = ("IS", "N", "TT")
                    params = (
                        dtype,
                        component.parameters.get("IS", 1e-14),
                        component.parameters.get("N", 1.0),
                        component.parameters.get("TT", 0)
                    )
                # Deduplicate model by parameters
                if params not in diode_models:
                    base = (
                        "DZEN" if dtype == "zener" else
                        "DSCH" if dtype == "schottky" else
                        "DSTD"
                    )
                    idx = model_id_counter[dtype]
                    model_name = f"{base}{idx}"
                    diode_models[params] = (model_name, dict((k, component.parameters.get(k)) for k in param_keys))
                    model_id_counter[dtype] += 1
                model_name, _ = diode_models[params]
                component.spice_model_name = model_name  # Attach for use in instance line

            elif component.comp_type == "led":
                led_models_used.add("LED_MODEL")
                component.spice_model_name = "LED_MODEL"

        # Add standard models
        lines.append("* --- Component Models ---")
        if led_models_used:
            lines.append(".MODEL LED_MODEL D(IS=1E-20 N=1.5 RS=0.1)")
        # Add all deduped diode models
        for model_name, param_dict in diode_models.values():
            param_text = " ".join(f"{k}={param_dict[k]}" for k in param_dict if param_dict[k] is not None)
            lines.append(f".model {model_name} D({param_text})")
        lines.append("")

        # Add components
        lines.append("* --- Circuit Components ---")
        for component in self.components:
            spice_line = component.to_spice()
            if spice_line:  # Skip empty lines (e.g., ground)
                lines.append(spice_line)

        lines.append("")

        # Add warnings as comments
        if self.warnings:
            lines.append("* --- Warnings ---")
            for warning in self.warnings:
                lines.append(f"* WARNING: {warning}")
            lines.append("")

        # End statement
        lines.append(".END")

        return "\n".join(lines)

    def get_node_list(self) -> List[str]:
        """Returns a list of all unique node names in the circuit."""
        nodes = set()
        for component in self.components:
            nodes.update(component.nodes)
        return sorted(list(nodes))

    def get_component_count(self) -> Dict[str, int]:
        """Returns a count of components by type."""
        counts: Dict[str, int] = {}
        for component in self.components:
            counts[component.comp_type] = counts.get(component.comp_type, 0) + 1
        return counts
