# ui/junction_item.py
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtCore import Qt, QPointF

from ui.undo_commands import MoveJunctionCommand
from ui.wire_segment_item import WireSegmentItem


class JunctionItem(QGraphicsEllipseItem):
    """Visual dot indicating a connection between 3+ wires."""
    GRID_SIZE = 10

    def __init__(self, x: float, y: float):
        # 10px diameter dot centered on the coordinate
        super().__init__(-5, -5, 10, 10)

        self.old_pos = None
        self.affected_wires = None
        self.setPos(x, y)

        # FIX: Ensure solid black fill and no border for a clean 'dot' look
        self.setBrush(QBrush(QColor("black"), Qt.SolidPattern))
        self.setPen(QPen(Qt.NoPen))

        # FIX: Set Z-Value high enough to sit on top of all wire segments (default 0)
        self.setZValue(5)

        self.setFlags(
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemSendsGeometryChanges
        )

    def scene_connection_point(self) -> QPointF:
        return self.scenePos()

    def _snap_to_grid(self, pos: QPointF) -> QPointF:
        """Calculates the nearest grid intersection for a given position."""
        x = round(pos.x() / self.GRID_SIZE) * self.GRID_SIZE
        y = round(pos.y() / self.GRID_SIZE) * self.GRID_SIZE
        return QPointF(x, y)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Snap the junction to the grid (10px or 25px as per your wire settings)
            grid = 10
            new_pos = self._snap_to_grid(value)

            # Inform the view/scene to stretch connected wires
            view = self.scene().views()[0]
            if hasattr(view, "_stretch_wires_at"):
                # Use the old position to find wires and new_pos to update them
                view._stretch_wires_at(self.pos(), new_pos)

            return new_pos
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        self.old_pos = self.pos()
        # Identify affected wires once at start of drag
        self.affected_wires = []
        view = self.scene().views()[0]
        for item in self.scene().items():
            if isinstance(item, WireSegmentItem) and not item.preview:
                line = item.line()
                p1_aff = (line.p1() == self.old_pos)
                p2_aff = (line.p2() == self.old_pos)
                if p1_aff or p2_aff:
                    self.affected_wires.append((item, p1_aff, p2_aff))
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        new_pos = self.pos()
        if self.old_pos != new_pos:
            view = self.scene().views()[0]
            command = MoveJunctionCommand(
                self, self.old_pos, new_pos, self.affected_wires
            )
            view.undo_stack.push(command)
