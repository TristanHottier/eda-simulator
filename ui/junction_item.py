from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QBrush, QColor


class JunctionItem(QGraphicsEllipseItem):
    GRID_SIZE = 50

    def __init__(self, x, y):
        super().__init__(-5, -5, 10, 10)
        self.setPos(x, y)
        self.setBrush(QColor(0, 0, 0))
        self.setPen(Qt.NoPen)
        self.setZValue(1.0)

        # Track wires connected to this junction
        self.connected_wires = set()

        self.setFlags(QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemSendsGeometryChanges)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Snapping logic
            new_pos = value
            grid_size = 50
            x = round(new_pos.x() / grid_size) * grid_size
            y = round(new_pos.y() / grid_size) * grid_size
            return QPointF(x, y)
        return super().itemChange(change, value)

    def scene_connection_point(self):
        return self.scenePos()

    def add_wire(self, wire):
        self.connected_wires.add(wire)

    def remove_wire(self, wire):
        self.connected_wires.discard(wire)