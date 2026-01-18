# ui/junction_item.py
from typing import Any
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtCore import Qt, QPointF

from ui. undo_commands import MoveJunctionCommand
from ui.wire_segment_item import WireSegmentItem


class JunctionItem(QGraphicsEllipseItem):
    """Visual dot indicating a connection between 3+ wires."""
    GRID_SIZE = 10

    def __init__(self, x:  float, y: float):
        # 10px diameter dot centered on the coordinate
        super().__init__(-5, -5, 10, 10)

        self.old_pos = None
        self.affected_wires = None
        self._is_being_moved_by_master = False  # Flag for multi-selection movement
        self._dark_mode = True  # Default to dark mode
        self.setPos(x, y)

        # Default to dark mode (white junctions)
        self. setBrush(QBrush(QColor("white"), Qt.SolidPattern))
        self.setPen(QPen(Qt.NoPen))

        # Set Z-Value high enough to sit on top of all wire segments
        self. setZValue(5)

        self.setFlags(
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemSendsGeometryChanges
        )

    def set_dark_mode(self, dark: bool) -> None:
        """Updates the junction color based on theme."""
        self._dark_mode = dark
        color = QColor("white") if dark else QColor("black")
        self.setBrush(QBrush(color, Qt.SolidPattern))

    def scene_connection_point(self) -> QPointF:
        return self.scenePos()

    def _snap_to_grid(self, pos: QPointF) -> QPointF:
        """Calculates the nearest grid intersection for a given position."""
        x = round(pos.x() / self.GRID_SIZE) * self.GRID_SIZE
        y = round(pos.y() / self.GRID_SIZE) * self.GRID_SIZE
        return QPointF(x, y)

    def _is_component_in_selection(self) -> bool:
        """Check if any ComponentItem is in the current selection."""
        from ui.component_item import ComponentItem

        if not self.scene():
            return False

        for item in self.scene().selectedItems():
            if isinstance(item, ComponentItem):
                return True
        return False

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # If being moved by a component (master), accept the position as-is
            if self._is_being_moved_by_master:
                new_pos = value
            else:
                # Check if a component is also selected
                if self._is_component_in_selection():
                    # Let the component handle our movement, don't move independently
                    return self.pos()

                # Junction moving alone - snap to 10px grid
                new_pos = self._snap_to_grid(value)

            # Inform the view/scene to stretch connected wires
            view = self.scene().views()[0]
            if hasattr(view, "_stretch_wires_at"):
                view._stretch_wires_at(self.pos(), new_pos)

            return new_pos
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        self.old_pos = self. pos()
        # Identify affected wires once at start of drag
        self. affected_wires = []
        view = self.scene().views()[0]
        for item in self.scene().items():
            if isinstance(item, WireSegmentItem) and not item.preview:
                line = item.line()
                p1_aff = (line.p1() == self. old_pos)
                p2_aff = (line.p2() == self.old_pos)
                if p1_aff or p2_aff:
                    self.affected_wires.append((item, p1_aff, p2_aff))
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        new_pos = self. pos()
        if self.old_pos != new_pos:
            view = self.scene().views()[0]
            command = MoveJunctionCommand(
                self, self. old_pos, new_pos, self.affected_wires
            )
            view.undo_stack.push(command)