from PySide6.QtWidgets import QGraphicsEllipseItem

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


class CreateWireCommand:
    def __init__(self, schematic_view, created_items, net_history_snapshot):
        self.view = schematic_view
        self.items = created_items  # This list now contains WireSegmentItems AND QGraphicsEllipseItems
        self.net_history = net_history_snapshot

    def undo(self):
        # 1. Remove all visual items from the scene
        for item in self.items:
            self.view.scene.removeItem(item)

            # 2. If the item is a junction, remove it from the tracking list
            if item in self.view.junctions:
                self.view.junctions.remove(item)

        # 3. Revert the net mapping
        self.view.point_to_net = self.net_history.copy()

    def redo(self):
        # 1. Add everything back to the scene
        for item in self.items:
            self.view.scene.addItem(item)

            # 2. Put junctions back into the tracking list
            if isinstance(item, QGraphicsEllipseItem) and item not in self.view.junctions:
                self.view.junctions.append(item)

            # 3. Re-register net points for wire segments
            if isinstance(item, WireSegmentItem):
                line = item.line()
                self.view.point_to_net[(line.x1(), line.y1())] = item.net_id
                self.view.point_to_net[(line.x2(), line.y2())] = item.net_id
