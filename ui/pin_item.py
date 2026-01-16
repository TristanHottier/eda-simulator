from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsRectItem
from PySide6.QtGui import QBrush, QColor
from PySide6.QtCore import Qt, QPointF


class PinItem(QGraphicsEllipseItem):
    """The visual representation of a Pin on the schematic."""

    def __init__(self, pin_logic, x, y, parent):
        super().__init__(-5, -5, 10, 10, parent)  # 10px diameter
        self.pin_logic = pin_logic  # Link to your Pin object from core/pin.py
        self.setPos(x, y)
        self.setBrush(QBrush(QColor("black")))
        self.setPen(Qt.NoPen)
        self.setZValue(1)

    def scene_connection_point(self):
        """Returns the center of the pin in _scene coordinates."""
        return self.mapToScene(QPointF(0, 0))