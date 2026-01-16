from PySide6.QtWidgets import QGraphicsEllipseItem

from ui.junction_item import JunctionItem
from ui.wire_segment_item import WireSegmentItem


class UndoStack:
    def __init__(self):
        self.stack = []
        self.index = -1  # points to last done

    def push(self, command):
        self.stack = self.stack[:self.index + 1]
        self.stack.append(command)
        command.redo()
        self.index += 1

    def undo(self):
        if self.index >= 0:
            self.stack[self.index].undo()
            self.index -= 1

    def redo(self):
        if self.index + 1 < len(self.stack):
            self.index += 1
            self.stack[self.index].redo()


# ui/undo_commands.py

class MoveComponentCommand:
    def __init__(self, component_item, old_pos, new_pos):
        self.component_item = component_item
        # Make sure to copy the positions as QPointF
        from PySide6.QtCore import QPointF
        self.old_pos = QPointF(old_pos)  # snapshot
        self.new_pos = QPointF(new_pos)

    def undo(self):
        self.component_item.setPos(self.old_pos)

    def redo(self):
        self.component_item.setPos(self.new_pos)


class ParameterChangeCommand:
    def __init__(self, component_model, key, old_value, new_value, component_item=None):
        self.model = component_model # This should be the core.component.Component object
        self.key = key
        self.old_value = old_value
        self.new_value = new_value
        self.component_item = component_item

    def undo(self):
        # Update the logical model
        self.model.parameters[self.key] = self.old_value
        # Refresh the UI label
        if self.component_item:
            self.component_item.update_label_after_dialog(self.model)

    def redo(self):
        # Update the logical model
        self.model.parameters[self.key] = self.new_value
        # Refresh the UI label
        if self.component_item:
            self.component_item.update_label_after_dialog(self.model)


class RotateComponentCommand:
    def __init__(self, component_item, old_rotation, new_rotation):
        self.component_item = component_item
        self.old_rotation = old_rotation
        self.new_rotation = new_rotation

    def undo(self):
        self.component_item.setRotation(self.old_rotation)

    def redo(self):
        self.component_item.setRotation(self.new_rotation)


# ui/undo_commands.py

class CreateWireCommand:
    # Add start_junction to the end of the argument list with a default of None
    def __init__(self, view, x1, y1, x2, y2, net_id, start_node=None, end_node=None, junction=None,
                 start_junction=None):
        self.view = view
        self.wire_coords = (x1, y1, x2, y2)
        self.net_id = net_id
        self.start_node = start_node
        self.end_node = end_node

        # We store both potential junctions
        self.end_junction = junction
        self.start_junction = start_junction

        self.wire_item = None

    def redo(self):
        from ui.wire_segment_item import WireSegmentItem
        x1, y1, x2, y2 = self.wire_coords
        self.wire_item = WireSegmentItem(x1, y1, x2, y2, self.net_id)

        # 1. Add wire to scene (Note: calling the scene method)
        scene = self.view.scene()
        scene.addItem(self.wire_item)

        if self.wire_item not in self.view.wires:
            self.view.wires.append(self.wire_item)

        # 2. Add junctions to scene and logical tracking
        for j in [self.start_junction, self.end_junction]:
            if j:
                if j.scene() is None:
                    scene.addItem(j)
                if j not in self.view.junctions:
                    self.view.junctions.append(j)

        # 3. Register wire with all connected nodes for stretching
        nodes = [self.start_node, self.end_node, self.start_junction, self.end_junction]
        for node in nodes:
            if node and hasattr(node, 'connected_wires'):
                # FIX: Use .add() instead of .append() because connected_wires is a set
                node.connected_wires.add(self.wire_item)

    def undo(self):
        scene = self.view.scene()

        # 1. Cleanup logical links
        nodes = [self.start_node, self.end_node, self.start_junction, self.end_junction]
        if self.wire_item:
            for node in nodes:
                if node and hasattr(node, 'connected_wires'):
                    # FIX: Use .discard() instead of .remove() for sets
                    # (discard doesn't raise an error if the item is already gone)
                    node.connected_wires.discard(self.wire_item)

            # 2. Remove wire
            scene.removeItem(self.wire_item)
            if self.wire_item in self.view.wires:
                self.view.wires.remove(self.wire_item)

        # 3. Remove junctions
        for j in [self.start_junction, self.end_junction]:
            if j:
                scene.removeItem(j)
                if j in self.view.junctions:
                    self.view.junctions.remove(j)


class DeleteCommand:
    def __init__(self, schematic_view, items):
        self.view = schematic_view
        self.items = items  # includes ComponentItems, WireSegmentItems, and now Junctions (EllipseItems)

        # Logical snapshots
        self.models = [item.model for item in items if hasattr(item, 'model')]
        self.junction_items = [item for item in items if isinstance(item, JunctionItem)]

        # Wire data storage
        self.wire_data = []
        for item in items:
            if isinstance(item, WireSegmentItem):
                line = item.line()
                self.wire_data.append(((line.x1(), line.y1()), (line.x2(), line.y2()), item.net_id))

    def redo(self):
        for item in self.items:
            self.view._scene.removeItem(item)
            # Remove from logical tracking
            if item in self.view.junctions:
                self.view.junctions.remove(item)

        for model in self.models:
            if model in self.view.components:
                self.view.components.remove(model)

        self.view.cleanup_junctions()

    def undo(self):
        for item in self.items:
            self.view._scene.addItem(item)
            # Restore to logical tracking
            if item in self.junction_items:
                self.view.junctions.append(item)

        for model in self.models:
            self.view.components.append(model)

        # Restore wire net logic
        for p1, p2, net_id in self.wire_data:
            self.view.point_to_net[p1] = net_id
            self.view.point_to_net[p2] = net_id
