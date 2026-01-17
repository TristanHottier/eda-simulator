# ui/wire_segment_item.py
from typing import Optional, Any
from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsItem, QWidget
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker, QPainter
from PySide6.QtCore import Qt, QPointF


class WireSegmentItem(QGraphicsLineItem):
    """
        Represents a single segment of an electrical connection.
        FIX: Updated GRID_SIZE to 25px for finer wire routing.
        """
    GRID_SIZE = 10  # Changed from 50

    def __init__(self, x1: float, y1: float, x2: float, y2: float,
                 net_id: Optional[int] = None, preview: bool = False):
        super().__init__(x1, y1, x2, y2)

        self.net_id = net_id
        self.preview = preview
        self.is_highlighted = False
        self.start_node = None  # Reference to PinItem or JunctionItem
        self.end_node = None

        if not self.preview:
            # Wires are selectable but NOT movable on their own
            self.setFlags(
                QGraphicsItem.ItemIsSelectable |
                QGraphicsItem.ItemSendsGeometryChanges
            )
            self.setAcceptHoverEvents(True)
            self.setAcceptedMouseButtons(Qt. LeftButton)

        # Standard wire styling
        self.base_pen = QPen(QColor(255, 0, 0), 2)
        self.base_pen. setCosmetic(True)
        self.base_pen.setCapStyle(Qt.RoundCap)

        if self.preview:
            self.base_pen. setStyle(Qt.DashLine)
            self.base_pen.setColor(QColor(255, 0, 0, 150))

        self.setPen(self.base_pen)

    def shape(self) -> QPainterPath:
        """Increases the hit-box of the wire for easier selection."""
        path = QPainterPath()
        path.moveTo(self.line().p1())
        path.lineTo(self.line().p2())

        stroker = QPainterPathStroker()
        stroker. setWidth(10)  # 10px virtual width for mouse detection
        return stroker.createStroke(path)

    def paint(self, painter: QPainter, option, widget: Optional[QWidget] = None) -> None:
        """Draws the wire with dynamic state (selection/glow)."""
        if self.isSelected():
            # Standard "Electric Blue" selection
            pen = QPen(QColor(0, 120, 215), 3)
            pen.setCosmetic(True)
        elif self.is_highlighted:
            # Subtle red glow for net-wide highlighting
            pen = QPen(QColor(220, 50, 50, 110), 6)
            pen.setCosmetic(True)
        else:
            pen = self.pen()

        painter.setPen(pen)
        painter.drawLine(self.line())

    def set_glow(self, enabled: bool) -> None:
        """Triggers a visual highlight of the segment."""
        if self.is_highlighted != enabled:
            self.is_highlighted = enabled
            self. update()

    def hoverEnterEvent(self, event) -> None:
        if not self.preview and self.net_id is not None:
            view = self.scene().views()[0]
            for wire in view.net_to_wires.get(self.net_id, []):
                wire.set_glow(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        if not self.preview and self.net_id is not None:
            view = self. scene().views()[0]
            for wire in view.net_to_wires. get(self.net_id, []):
                wire.set_glow(False)
        super().hoverLeaveEvent(event)