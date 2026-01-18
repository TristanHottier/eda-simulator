# ui/pin_item. py
from PySide6.QtWidgets import QGraphicsEllipseItem
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtCore import Qt, QPointF


class PinItem(QGraphicsEllipseItem):
    """Visual dot representing a component terminal."""

    def __init__(self, pin_logic, x: float, y: float, parent):
        # 8px diameter dot for pins (slightly smaller than junctions)
        super().__init__(-4, -4, 8, 8, parent)

        self.pin_logic = pin_logic
        self.setPos(QPointF(x, y))

        # Default to dark mode (white pins)
        self._dark_mode = True
        self.setBrush(QBrush(QColor("white"), Qt.SolidPattern))
        self.setPen(QPen(Qt.NoPen))

        # Ensure it renders above the parent component's body
        self.setZValue(5)

    def set_dark_mode(self, dark:  bool) -> None:
        """Updates the pin color based on theme."""
        self._dark_mode = dark
        color = QColor("white") if dark else QColor("black")
        self.setBrush(QBrush(color, Qt.SolidPattern))

    def scene_connection_point(self) -> QPointF:
        # Maps the center of the pin to the global scene coordinates
        return self.mapToScene(QPointF(0, 0))