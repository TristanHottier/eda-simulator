# ui/undo_commands.py
from typing import List, Tuple, Any, Optional, TYPE_CHECKING
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsItem

if TYPE_CHECKING:
    from ui.schematic_view import SchematicView
    from ui.junction_item import JunctionItem
    from ui.wire_segment_item import WireSegmentItem


class UndoStack:
    """Manages a history of commands for undo/redo functionality."""

    def __init__(self):
        self.stack: List[Any] = []
        self.index: int = -1  # Points to the last executed command

    def push(self, command: Any) -> None:
        """Adds a new command to the stack and executes its redo action."""
        self.stack = self.stack[:self.index + 1]
        self.stack.append(command)
        command.redo()
        self.index += 1

    def undo(self) -> None:
        if self.index >= 0:
            self.stack[self.index].undo()
            self.index -= 1

    def redo(self) -> None:
        if self.index + 1 < len(self.stack):
            self.index += 1
            self.stack[self.index].redo()


class MoveComponentCommand:
    """Handles position changes for component items."""

    def __init__(self, component_item, old_pos: QPointF, new_pos: QPointF):
        self.item = component_item
        self.old_pos = QPointF(old_pos)
        self.new_pos = QPointF(new_pos)

    def undo(self):
        self.item.setPos(self.old_pos)

    def redo(self):
        self.item.setPos(self.new_pos)


class RotateComponentCommand:
    """Handles 90-degree rotations for component items."""

    def __init__(self, component_item, old_rot: float, new_rot: float):
        self.item = component_item
        self.old_rot = old_rot
        self.new_rot = new_rot

    def undo(self):
        self.item.setRotation(self.old_rot)

    def redo(self):
        self.item.setRotation(self.new_rot)


class CreateWireCommand:
    """Handles the addition of new wire segments to the schematic."""

    def __init__(self, view: 'SchematicView', wire_item: 'WireSegmentItem'):
        self.view = view
        self.wire = wire_item

    def undo(self):
        # FIX: Only remove if the item is actually in the scene
        if self.wire.scene() == self.view._scene:
            self.view._scene.removeItem(self.wire)
        # Net cleanup is handled dynamically by SchematicView
        self.view.cleanup_junctions()

    def redo(self):
        # FIX: Only add if the item is not already in the scene
        if not self.wire.scene():
            self.view._scene.addItem(self.wire)
        self.view.register_wire_connection(self.wire)


class ParameterChangeCommand:
    """Handles updates to component model parameters and visual labels."""

    def __init__(self, model, key: str, old_val: Any, new_val: Any, component_item=None):
        self.model = model
        self.key = key
        self.old_val = old_val
        self.new_val = new_val
        self.item = component_item

    def undo(self):
        self.model.parameters[self.key] = self.old_val
        if self.item:
            self.item.refresh_label()

    def redo(self):
        self.model.parameters[self.key] = self.new_val
        if self.item:
            self.item.refresh_label()


class DeleteItemsCommand:
    """Handles batch deletion of components, wires, and junctions."""

    def __init__(self, view: 'SchematicView', items: List[QGraphicsItem]):
        from ui.junction_item import JunctionItem
        from ui.wire_segment_item import WireSegmentItem

        self.view = view
        self.items = items
        self.models = [item.model for item in items if hasattr(item, 'model')]
        self.junction_items = [item for item in items if isinstance(item, JunctionItem)]
        self.wire_snapshot = []

        for item in self.items:
            if isinstance(item, WireSegmentItem):
                line = item.line()
                self.wire_snapshot.append(((line.x1(), line.y1()), (line.x2(), line.y2()), item.net_id))

    def redo(self):
        # Remove items from the scene safely
        for item in self.items:
            # Check if the item is still in the scene before removing
            if item.scene() == self.view._scene:
                self.view._scene.removeItem(item)

            # Handle junctions explicitly
            if item in self.view.junctions:
                self.view.junctions.remove(item)

        # Remove models from components safely
        for model in self.models:
            if model in self.view.components:
                self.view.components.remove(model)

        # Clean up junctions after deletions
        self.view.cleanup_junctions()

    def undo(self):
        # Restore items to the scene safely
        for item in self.items:
            # Prevent adding duplicates to the scene
            if not item.scene():
                self.view._scene.addItem(item)

            # Restore junctions explicitly
            if item in self.junction_items and item not in self.view.junctions:
                self.view.junctions.append(item)

        # Restore models to components safely
        for model in self.models:
            if model not in self.view.components:
                self.view.components.append(model)

        # Restore wires to point_to_net mapping
        for (p1, p2, net_id) in self.wire_snapshot:
            if p1 not in self.view.point_to_net:
                self.view.point_to_net[p1] = net_id
            if p2 not in self.view.point_to_net:
                self.view.point_to_net[p2] = net_id

        # Clean up junctions after restoration
        self.view.cleanup_junctions()


# ui/undo_commands.py
from PySide6.QtGui import QUndoCommand, QColor
from PySide6.QtCore import QPointF


class MoveJunctionCommand(QUndoCommand):
    """
    Groups the movement of a junction and the stretching of
    all connected wires into one undo/redo action.
    """

    def __init__(self, junction, old_pos, new_pos, affected_wires):
        super().__init__("Move Junction")
        self.junction = junction
        self.old_pos = old_pos
        self.new_pos = new_pos
        # List of tuples: (wire_item, is_p1_affected, is_p2_affected)
        self.affected_wires = affected_wires

    def redo(self):
        self.junction.setPos(self.new_pos)
        self._update_wires(self.new_pos)

    def undo(self):
        self.junction.setPos(self.old_pos)
        self._update_wires(self.old_pos)

    def _update_wires(self, target_pos):
        for wire, p1_aff, p2_aff in self.affected_wires:
            line = wire.line()
            x1 = target_pos.x() if p1_aff else line.x1()
            y1 = target_pos.y() if p1_aff else line.y1()
            x2 = target_pos.x() if p2_aff else line.x2()
            y2 = target_pos.y() if p2_aff else line.y2()
            wire.setLine(x1, y1, x2, y2)


class FlipComponentCommand:
    """Handles horizontal or vertical flipping for component items."""

    def __init__(self, component_item, axis: str):
        """
        Args:
            component_item: The ComponentItem to flip.
            axis: 'h' for horizontal flip, 'v' for vertical flip.
        """
        self.item = component_item
        self.axis = axis

    def undo(self):
        # Flipping is its own inverse, so undo == redo
        self._apply_flip()

    def redo(self):
        self._apply_flip()

    def _apply_flip(self):
        transform = self.item.transform()
        if self.axis == 'h':
            # Horizontal flip: mirror along Y-axis (negate X scale)
            self.item.setTransform(transform.scale(-1, 1))
        else:
            # Vertical flip: mirror along X-axis (negate Y scale)
            self.item.setTransform(transform.scale(1, -1))


class PasteItemsCommand:
    """Handles pasting of copied components and wires."""

    def __init__(self, view: 'SchematicView', component_items: List, wire_items: List):
        self.view = view
        self.component_items = component_items
        self.wire_items = wire_items
        self.models = [item.model for item in component_items]

    def redo(self):
        # Add components to scene
        for item in self.component_items:
            if not item.scene():
                self.view._scene.addItem(item)
            item.setSelected(True)

        # Add component models to tracking list
        for model in self.models:
            if model not in self.view.components:
                self.view.components.append(model)

        # Add wires to scene and register connections
        for wire in self.wire_items:
            if not wire.scene():
                self.view._scene.addItem(wire)
                self.view.register_wire_connection(wire)
            wire.setSelected(True)

        self.view.cleanup_junctions()

        # Select junctions belonging to pasted wires
        self._select_pasted_junctions()

    def undo(self):
        # Remove wires from scene
        for wire in self.wire_items:
            if wire.scene() == self.view._scene:
                self.view._scene.removeItem(wire)

        # Remove components from scene
        for item in self.component_items:
            if item.scene() == self.view._scene:
                self.view._scene.removeItem(item)

        # Remove models from tracking list
        for model in self.models:
            if model in self.view.components:
                self.view.components.remove(model)

        self.view.cleanup_junctions()

    def _select_pasted_junctions(self):
        """Selects all junctions that belong to the pasted wires."""
        # Collect all endpoints of pasted wires
        pasted_endpoints = set()
        for wire in self.wire_items:
            line = wire.line()
            pasted_endpoints.add((line.x1(), line.y1()))
            pasted_endpoints.add((line.x2(), line.y2()))

        # Select junctions at those endpoints
        for junction in self.view.junctions:
            junction_pos = (junction.pos().x(), junction.pos().y())
            if junction_pos in pasted_endpoints:
                junction.setSelected(True)


class WireColorChangeCommand:
    """Handles wire color changes with undo/redo support."""

    def __init__(self, wires: List, old_colors: List[QColor], new_color:  QColor):
        """
        Args:
            wires: List of WireSegmentItem to change color.
            old_colors: List of original QColors (same order as wires).
            new_color:  The new QColor to apply.
        """
        self.wires = wires
        self.old_colors = [QColor(c) for c in old_colors]  # Copy colors
        self.new_color = QColor(new_color)

    def undo(self):
        for wire, old_color in zip(self.wires, self.old_colors):
            wire.set_color(old_color)

    def redo(self):
        for wire in self.wires:
            wire.set_color(self. new_color)
