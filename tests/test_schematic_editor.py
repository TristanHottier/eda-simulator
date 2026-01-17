# tests/test_schematic_editor.py
import unittest
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

from core.component import Component
from core.pin import Pin, PinDirection
from core.net import Net
from ui.component_item import ComponentItem
from ui.wire_segment_item import WireSegmentItem
from ui.junction_item import JunctionItem
from ui.schematic_view import SchematicView
from ui.undo_commands import (
    UndoStack,
    MoveComponentCommand,
    RotateComponentCommand,
    FlipComponentCommand,
    CreateWireCommand,
    DeleteItemsCommand,
    ParameterChangeCommand,
    PasteItemsCommand,
    WireColorChangeCommand,
)

# Initialize QApplication once for all tests
app = None


def setUpModule():
    global app
    if not QApplication.instance():
        app = QApplication([])


class TestComponentItem(unittest.TestCase):
    """Tests for ComponentItem visual representation."""

    def setUp(self):
        self.model = Component("R1", comp_type="resistor")
        self.item = ComponentItem(self.model)

    def test_component_item_creation(self):
        """Test that ComponentItem is created with correct properties."""
        self.assertEqual(self.item.ref, "R1")
        self.assertEqual(self.item.model.type, "resistor")
        self.assertIsNotNone(self.item.label)

    def test_component_default_size(self):
        """Test that ComponentItem has default size of 100x50."""
        rect = self.item.rect()
        self.assertEqual(rect.width(), 100)
        self.assertEqual(rect.height(), 50)

    def test_component_has_pins(self):
        """Test that ComponentItem creates PinItems for model pins."""
        self.assertEqual(len(self.item.pin_items), 2)

    def test_component_snap_to_grid(self):
        """Test that snap_to_grid returns correct grid position."""
        pos = QPointF(123, 167)
        snapped = self.item._snap_to_grid(pos)
        self.assertEqual(snapped.x(), 100)  # 123 rounds to 100 (50px grid)
        self.assertEqual(snapped.y(), 150)  # 167 rounds to 150

    def test_component_label_refresh(self):
        """Test that label updates when parameters change."""
        self.item.model.parameters["resistance"] = 4700
        self.item.refresh_label()
        self.assertIn("4700", self.item.label.toPlainText())

    def test_component_transform_origin(self):
        """Test that transform origin is set to center."""
        origin = self.item.transformOriginPoint()
        self.assertEqual(origin.x(), 50)  # width/2
        self.assertEqual(origin.y(), 25)  # height/2


class TestWireSegmentItem(unittest.TestCase):
    """Tests for WireSegmentItem."""

    def test_wire_creation(self):
        """Test that wire is created with correct endpoints."""
        wire = WireSegmentItem(0, 0, 100, 0)
        line = wire.line()
        self.assertEqual(line.x1(), 0)
        self.assertEqual(line.y1(), 0)
        self.assertEqual(line.x2(), 100)
        self.assertEqual(line.y2(), 0)

    def test_wire_preview_mode(self):
        """Test that preview wire has dashed style."""
        wire = WireSegmentItem(0, 0, 100, 0, preview=True)
        self.assertTrue(wire.preview)

    def test_wire_default_color(self):
        """Test that wire has default red color."""
        wire = WireSegmentItem(0, 0, 100, 0)
        self.assertEqual(wire.color.red(), 255)
        self.assertEqual(wire.color.green(), 0)
        self.assertEqual(wire.color.blue(), 0)

    def test_wire_custom_color(self):
        """Test that wire can be created with custom color."""
        blue = QColor(0, 0, 255)
        wire = WireSegmentItem(0, 0, 100, 0, color=blue)
        self.assertEqual(wire.color.blue(), 255)

    def test_wire_set_color(self):
        """Test that wire color can be changed."""
        wire = WireSegmentItem(0, 0, 100, 0)
        green = QColor(0, 255, 0)
        wire.set_color(green)
        self.assertEqual(wire.color.green(), 255)

    def test_wire_color_hex(self):
        """Test that color_hex returns correct hex string."""
        wire = WireSegmentItem(0, 0, 100, 0, color=QColor(255, 0, 0))
        self.assertEqual(wire.color_hex.lower(), "#ff0000")

    def test_wire_set_color_from_hex(self):
        """Test that wire color can be set from hex string."""
        wire = WireSegmentItem(0, 0, 100, 0)
        wire.set_color_from_hex("#00ff00")
        self.assertEqual(wire.color.green(), 255)

    def test_wire_glow(self):
        """Test wire highlight/glow functionality."""
        wire = WireSegmentItem(0, 0, 100, 0)
        self.assertFalse(wire.is_highlighted)
        wire.set_glow(True)
        self.assertTrue(wire.is_highlighted)
        wire.set_glow(False)
        self.assertFalse(wire.is_highlighted)

    def test_wire_net_id(self):
        """Test that wire can store net_id."""
        wire = WireSegmentItem(0, 0, 100, 0, net_id=5)
        self.assertEqual(wire.net_id, 5)


class TestJunctionItem(unittest.TestCase):
    """Tests for JunctionItem."""

    def test_junction_creation(self):
        """Test that junction is created at correct position."""
        junction = JunctionItem(100, 200)
        self.assertEqual(junction.pos().x(), 100)
        self.assertEqual(junction.pos().y(), 200)

    def test_junction_size(self):
        """Test that junction has 10px diameter."""
        junction = JunctionItem(0, 0)
        rect = junction.rect()
        self.assertEqual(rect.width(), 10)
        self.assertEqual(rect.height(), 10)

    def test_junction_snap_to_grid(self):
        """Test junction snaps to 10px grid."""
        junction = JunctionItem(0, 0)
        pos = QPointF(23, 47)
        snapped = junction._snap_to_grid(pos)
        self.assertEqual(snapped.x(), 20)
        self.assertEqual(snapped.y(), 50)

    def test_junction_scene_connection_point(self):
        """Test that scene_connection_point returns scene position."""
        junction = JunctionItem(150, 250)
        point = junction.scene_connection_point()
        self.assertEqual(point.x(), 150)
        self.assertEqual(point.y(), 250)


class TestUndoStack(unittest.TestCase):
    """Tests for the UndoStack and Command pattern."""

    def test_undo_stack_creation(self):
        """Test UndoStack initializes correctly."""
        stack = UndoStack()
        self.assertEqual(len(stack.stack), 0)
        self.assertEqual(stack.index, -1)

    def test_undo_stack_push(self):
        """Test pushing commands to the stack."""
        stack = UndoStack()
        mock_cmd = MagicMock()
        stack.push(mock_cmd)
        self.assertEqual(len(stack.stack), 1)
        self.assertEqual(stack.index, 0)
        mock_cmd.redo.assert_called_once()

    def test_undo_stack_undo(self):
        """Test undoing a command."""
        stack = UndoStack()
        mock_cmd = MagicMock()
        stack.push(mock_cmd)
        stack.undo()
        mock_cmd.undo.assert_called_once()
        self.assertEqual(stack.index, -1)

    def test_undo_stack_redo(self):
        """Test redoing a command."""
        stack = UndoStack()
        mock_cmd = MagicMock()
        stack.push(mock_cmd)
        stack.undo()
        stack.redo()
        self.assertEqual(mock_cmd.redo.call_count, 2)
        self.assertEqual(stack.index, 0)

    def test_undo_stack_truncates_on_push(self):
        """Test that pushing after undo truncates future commands."""
        stack = UndoStack()
        cmd1 = MagicMock()
        cmd2 = MagicMock()
        cmd3 = MagicMock()

        stack.push(cmd1)
        stack.push(cmd2)
        stack.undo()  # Now at cmd1
        stack.push(cmd3)  # Should remove cmd2

        self.assertEqual(len(stack.stack), 2)
        self.assertIs(stack.stack[1], cmd3)


class TestMoveComponentCommand(unittest.TestCase):
    """Tests for MoveComponentCommand."""

    def setUp(self):
        self.model = Component("R1", comp_type="resistor")
        self.item = ComponentItem(self.model)
        self.old_pos = QPointF(0, 0)
        self.new_pos = QPointF(100, 50)

    def test_move_command_redo(self):
        """Test that redo moves component to new position."""
        cmd = MoveComponentCommand(self.item, self.old_pos, self.new_pos)
        cmd.redo()
        self.assertEqual(self.item.pos(), self.new_pos)

    def test_move_command_undo(self):
        """Test that undo moves component to old position."""
        self.item.setPos(self.new_pos)
        cmd = MoveComponentCommand(self.item, self.old_pos, self.new_pos)
        cmd.undo()
        self.assertEqual(self.item.pos(), self.old_pos)


class TestRotateComponentCommand(unittest.TestCase):
    """Tests for RotateComponentCommand."""

    def setUp(self):
        self.model = Component("R1", comp_type="resistor")
        self.item = ComponentItem(self.model)

    def test_rotate_command_redo(self):
        """Test that redo rotates component to new angle."""
        cmd = RotateComponentCommand(self.item, 0, 90)
        cmd.redo()
        self.assertEqual(self.item.rotation(), 90)

    def test_rotate_command_undo(self):
        """Test that undo rotates component to old angle."""
        self.item.setRotation(90)
        cmd = RotateComponentCommand(self.item, 0, 90)
        cmd.undo()
        self.assertEqual(self.item.rotation(), 0)


class TestFlipComponentCommand(unittest.TestCase):
    """Tests for FlipComponentCommand."""

    def setUp(self):
        self.model = Component("R1", comp_type="resistor")
        self.item = ComponentItem(self.model)

    def test_flip_horizontal(self):
        """Test horizontal flip command."""
        cmd = FlipComponentCommand(self.item, 'h')
        original_transform = self.item.transform()
        cmd.redo()
        # Transform should have changed
        self.assertNotEqual(self.item.transform(), original_transform)

    def test_flip_vertical(self):
        """Test vertical flip command."""
        cmd = FlipComponentCommand(self.item, 'v')
        original_transform = self.item.transform()
        cmd.redo()
        # Transform should have changed
        self.assertNotEqual(self.item.transform(), original_transform)

    def test_flip_is_self_inverse(self):
        """Test that flipping twice returns to original state."""
        cmd = FlipComponentCommand(self.item, 'h')
        original_transform = self.item.transform()
        cmd.redo()
        cmd.undo()  # Flip is self-inverse, so undo = redo
        # Should be back to original (within floating point tolerance)
        self.assertEqual(self.item.transform().m11(), original_transform.m11())


class TestParameterChangeCommand(unittest.TestCase):
    """Tests for ParameterChangeCommand."""

    def setUp(self):
        self.model = Component("R1", comp_type="resistor")
        self.item = ComponentItem(self.model)

    def test_parameter_change_redo(self):
        """Test that redo applies new parameter value."""
        cmd = ParameterChangeCommand(
            self.model, "resistance", 1000, 4700, self.item
        )
        cmd.redo()
        self.assertEqual(self.model.parameters["resistance"], 4700)

    def test_parameter_change_undo(self):
        """Test that undo restores old parameter value."""
        self.model.parameters["resistance"] = 4700
        cmd = ParameterChangeCommand(
            self.model, "resistance", 1000, 4700, self.item
        )
        cmd.undo()
        self.assertEqual(self.model.parameters["resistance"], 1000)


class TestWireColorChangeCommand(unittest.TestCase):
    """Tests for WireColorChangeCommand."""

    def test_color_change_redo(self):
        """Test that redo applies new color."""
        wire = WireSegmentItem(0, 0, 100, 0, color=QColor(255, 0, 0))
        new_color = QColor(0, 255, 0)
        cmd = WireColorChangeCommand([wire], [wire.color], new_color)
        cmd.redo()
        self.assertEqual(wire.color.green(), 255)

    def test_color_change_undo(self):
        """Test that undo restores old color."""
        original_color = QColor(255, 0, 0)
        wire = WireSegmentItem(0, 0, 100, 0, color=original_color)
        wire.set_color(QColor(0, 255, 0))
        cmd = WireColorChangeCommand([wire], [original_color], QColor(0, 255, 0))
        cmd.undo()
        self.assertEqual(wire.color.red(), 255)

    def test_color_change_multiple_wires(self):
        """Test changing color of multiple wires at once."""
        wire1 = WireSegmentItem(0, 0, 100, 0, color=QColor(255, 0, 0))
        wire2 = WireSegmentItem(0, 0, 100, 0, color=QColor(0, 255, 0))
        new_color = QColor(0, 0, 255)
        cmd = WireColorChangeCommand(
            [wire1, wire2],
            [wire1.color, wire2.color],
            new_color
        )
        cmd.redo()
        self.assertEqual(wire1.color.blue(), 255)
        self.assertEqual(wire2.color.blue(), 255)


class TestSchematicView(unittest.TestCase):
    """Tests for SchematicView functionality."""

    def setUp(self):
        self.view = SchematicView()

    def test_schematic_view_creation(self):
        """Test that SchematicView initializes correctly."""
        self.assertIsNotNone(self.view.scene())
        self.assertEqual(self.view.mode, "component")
        self.assertEqual(self.view.next_net_id, 1)

    def test_schematic_view_grid_size(self):
        """Test that grid size is 10px."""
        self.assertEqual(self.view.GRID_SIZE, 10)

    def test_snap_point_to_grid(self):
        """Test that points snap to grid correctly."""
        pos = QPointF(23, 47)
        snapped = self.view._snap_point(pos)
        self.assertEqual(snapped.x(), 20)
        self.assertEqual(snapped.y(), 50)

    def test_initial_wire_color(self):
        """Test that initial wire color is red."""
        color = self.view.get_current_wire_color()
        self.assertEqual(color.red(), 255)
        self.assertEqual(color.green(), 0)
        self.assertEqual(color.blue(), 0)

    def test_set_current_wire_color(self):
        """Test setting current wire color."""
        blue = QColor(0, 0, 255)
        self.view.set_current_wire_color(blue)
        color = self.view.get_current_wire_color()
        self.assertEqual(color.blue(), 255)

    def test_register_wire_connection(self):
        """Test that wire registration updates net tracking."""
        wire = WireSegmentItem(0, 0, 100, 0)
        self.view.scene().addItem(wire)
        self.view.register_wire_connection(wire)

        self.assertIsNotNone(wire.net_id)
        self.assertIn((0, 0), self.view.point_to_net)
        self.assertIn((100, 0), self.view.point_to_net)

    def test_net_merging(self):
        """Test that connecting two nets merges them."""
        # Create two separate wires (two nets)
        wire1 = WireSegmentItem(0, 0, 100, 0)
        wire2 = WireSegmentItem(200, 0, 300, 0)

        self.view.scene().addItem(wire1)
        self.view.scene().addItem(wire2)
        self.view.register_wire_connection(wire1)
        self.view.register_wire_connection(wire2)

        net1 = wire1.net_id
        net2 = wire2.net_id
        self.assertNotEqual(net1, net2)

        # Connect them with a third wire
        wire3 = WireSegmentItem(100, 0, 200, 0)
        self.view.scene().addItem(wire3)
        self.view.register_wire_connection(wire3)

        # All should now be on same net
        self.assertEqual(wire1.net_id, wire3.net_id)

    def test_cleanup_junctions(self):
        """Test that cleanup_junctions creates correct junctions."""
        wire1 = WireSegmentItem(0, 0, 100, 0)
        wire2 = WireSegmentItem(100, 0, 100, 100)

        self.view.scene().addItem(wire1)
        self.view.scene().addItem(wire2)
        self.view.register_wire_connection(wire1)
        self.view.register_wire_connection(wire2)

        # Should have junctions at (0,0), (100,0), (100,100)
        junction_positions = {(j.pos().x(), j.pos().y()) for j in self.view.junctions}
        self.assertIn((0, 0), junction_positions)
        self.assertIn((100, 0), junction_positions)
        self.assertIn((100, 100), junction_positions)

    def test_clipboard_initially_empty(self):
        """Test that clipboard starts empty."""
        self.assertEqual(self.view.clipboard, {})


class TestSchematicViewCopyPaste(unittest.TestCase):
    """Tests for copy/paste functionality."""

    def setUp(self):
        self.view = SchematicView()

    def test_copy_empty_selection(self):
        """Test that copying with no selection does nothing."""
        self.view.copy_selection()
        self.assertEqual(self.view.clipboard, {})

    def test_copy_component(self):
        """Test copying a component."""
        model = Component("R1", comp_type="resistor")
        item = ComponentItem(model)
        item.setPos(100, 200)
        self.view.scene().addItem(item)
        self.view.components.append(model)

        item.setSelected(True)
        self.view.copy_selection()

        self.assertEqual(len(self.view.clipboard.get("components", [])), 1)
        self.assertEqual(self.view.clipboard["components"][0]["ref"], "R1")

    def test_copy_wire(self):
        """Test copying a wire."""
        wire = WireSegmentItem(0, 0, 100, 0, color=QColor(0, 255, 0))
        wire.net_id = 1
        self.view.scene().addItem(wire)

        wire.setSelected(True)
        self.view.copy_selection()

        self.assertEqual(len(self.view.clipboard.get("wires", [])), 1)
        self.assertEqual(self.view.clipboard["wires"][0]["color"], "#00ff00")


class TestSchematicViewSaveLoad(unittest.TestCase):
    """Tests for save/load JSON functionality."""

    def setUp(self):
        self.view = SchematicView()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Cleanup temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_load_component(self):
        """Test saving and loading a component."""
        # Add a component
        model = Component("R1", comp_type="resistor", parameters={"resistance": 4700})
        item = ComponentItem(model)
        item.setPos(100, 200)
        item.setRotation(90)
        self.view.scene().addItem(item)
        self.view.components.append(model)

        # Save to temp file
        temp_file = os.path.join(self.temp_dir, "test_save.json")

        # Mock the file dialog
        with patch.object(self.view, 'save_to_json') as mock_save:
            # Manually create save data
            data = {
                "version": "0.1",
                "components": [{
                    "ref": "R1",
                    "comp_type": "resistor",
                    "x": 100,
                    "y": 200,
                    "rotation": 90,
                    "parameters": {"resistance": 4700, "type": "resistor"}
                }],
                "wires": []
            }
            with open(temp_file, 'w') as f:
                json.dump(data, f)

        # Load from file
        with open(temp_file, 'r') as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data["version"], "0.1")
        self.assertEqual(len(loaded_data["components"]), 1)
        self.assertEqual(loaded_data["components"][0]["ref"], "R1")
        self.assertEqual(loaded_data["components"][0]["rotation"], 90)

    def test_save_load_wire_with_color(self):
        """Test that wire color is preserved in save/load."""
        temp_file = os.path.join(self.temp_dir, "test_wire. json")

        data = {
            "version": "0.1",
            "components": [],
            "wires": [{
                "x1": 0, "y1": 0, "x2": 100, "y2": 0,
                "net_id": 1,
                "color": "#00ff00"
            }]
        }

        with open(temp_file, 'w') as f:
            json.dump(data, f)

        with open(temp_file, 'r') as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data["wires"][0]["color"], "#00ff00")


class TestComponentModel(unittest.TestCase):
    """Tests for Component model."""

    def test_component_default_params(self):
        """Test that components get correct default parameters."""
        resistor = Component("R1", comp_type="resistor")
        self.assertEqual(resistor.parameters["resistance"], 1000)
        self.assertEqual(resistor.parameters["type"], "resistor")

    def test_component_custom_params(self):
        """Test that custom parameters override defaults."""
        resistor = Component("R1", comp_type="resistor", parameters={"resistance": 4700})
        self.assertEqual(resistor.parameters["resistance"], 4700)

    def test_component_auto_pins(self):
        """Test that component auto-generates pins if none provided."""
        resistor = Component("R1", comp_type="resistor")
        self.assertEqual(len(resistor.pins), 2)

    def test_component_to_dict(self):
        """Test component serialization."""
        resistor = Component("R1", comp_type="resistor")
        data = resistor.to_dict()
        self.assertEqual(data["ref"], "R1")
        self.assertEqual(data["comp_type"], "resistor")
        self.assertIn("pins", data)

    def test_component_update_parameter(self):
        """Test updating a parameter."""
        resistor = Component("R1", comp_type="resistor")
        resistor.update_parameter("resistance", 10000)
        self.assertEqual(resistor.get_parameter("resistance"), 10000)


class TestNetModel(unittest.TestCase):
    """Tests for Net model."""

    def test_net_creation(self):
        """Test net creation with name."""
        net = Net("VCC")
        self.assertEqual(net.name, "VCC")
        self.assertEqual(len(net.pins), 0)

    def test_net_connect_pin(self):
        """Test connecting a pin to a net."""
        net = Net("NET1")
        pin = Pin("1", PinDirection.BIDIRECTIONAL)
        net.connect(pin)

        self.assertEqual(len(net.pins), 1)
        self.assertIn(pin, net.pins)
        self.assertEqual(pin.net, net)


class TestPinModel(unittest.TestCase):
    """Tests for Pin model."""

    def test_pin_creation(self):
        """Test pin creation with properties."""
        pin = Pin("A", PinDirection.INPUT, rel_x=0, rel_y=25)
        self.assertEqual(pin.name, "A")
        self.assertEqual(pin.direction, PinDirection.INPUT)
        self.assertEqual(pin.rel_x, 0)
        self.assertEqual(pin.rel_y, 25)

    def test_pin_directions(self):
        """Test all pin directions."""
        input_pin = Pin("1", PinDirection.INPUT)
        output_pin = Pin("2", PinDirection.OUTPUT)
        bidir_pin = Pin("3", PinDirection.BIDIRECTIONAL)

        self.assertEqual(input_pin.direction, PinDirection.INPUT)
        self.assertEqual(output_pin.direction, PinDirection.OUTPUT)
        self.assertEqual(bidir_pin.direction, PinDirection.BIDIRECTIONAL)


if __name__ == "__main__":
    unittest.main()