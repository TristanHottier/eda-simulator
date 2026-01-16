# ui/junction_item.py
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtCore import Qt, QPointF


class JunctionItem(QGraphicsEllipseItem):
    """Visual dot indicating a connection between 3+ wires."""

    def __init__(self, x: float, y: float):
        # 10px diameter dot centered on the coordinate
        super().__init__(-5, -5, 10, 10)

        self.setPos(x, y)

        # FIX: Ensure solid black fill and no border for a clean 'dot' look
        self.setBrush(QBrush(QColor("black"), Qt.SolidPattern))
        self.setPen(QPen(Qt.NoPen))

        # FIX: Set Z-Value high enough to sit on top of all wire segments (default 0)
        self.setZValue(10)

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
        """Handles snapping during item movement."""
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            return self._snap_to_grid(value)
        return super().itemChange(change, value)
