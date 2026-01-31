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
    GRID_SIZE = 25  # Changed from 50

    DEFAULT_COLOR = QColor(255, 0, 0)  # Red

    def __init__(self, x1: float, y1: float, x2: float, y2: float,
                 net_id: Optional[int] = None, preview:  bool = False,
                 color: QColor = None):
        super().__init__(x1, y1, x2, y2)

        self.net_id = net_id
        self.preview = preview
        self.is_highlighted = False
        self.start_node = None  # Reference to PinItem or JunctionItem
        self.end_node = None

        # Wire color (stored as QColor)
        self._color = QColor(color) if color else QColor(self.DEFAULT_COLOR)

        if not self.preview:
            # Wires are selectable but NOT movable on their own
            self.setFlags(
                QGraphicsItem.ItemIsSelectable |
                QGraphicsItem.ItemSendsGeometryChanges
            )
            self.setAcceptHoverEvents(True)
            self.setAcceptedMouseButtons(Qt.LeftButton)

        # Standard wire styling
        self._update_pen()

    def _update_pen(self) -> None:
        """Updates the pen based on current color setting."""
        self.base_pen = QPen(self._color, 2)
        self.base_pen.setCosmetic(True)
        self.base_pen.setCapStyle(Qt.RoundCap)

        if self.preview:
            self.base_pen.setStyle(Qt.DashLine)
            # Make preview slightly transparent but use wire's color
            preview_color = QColor(self._color)
            preview_color.setAlpha(180)
            self.base_pen.setColor(preview_color)

        self.setPen(self.base_pen)

    @property
    def color(self) -> QColor:
        """Returns the current color."""
        return self._color

    @property
    def color_hex(self) -> str:
        """Returns the current color as a hex string for serialization."""
        return self._color.name()

    def set_color(self, color: QColor) -> None:
        """Sets the wire color."""
        self._color = QColor(color)
        self._update_pen()
        self.update()

    def set_color_from_hex(self, hex_color: str) -> None:
        """Sets the wire color from a hex string."""
        self._color = QColor(hex_color)
        self._update_pen()
        self.update()

    def shape(self) -> QPainterPath:
        """Increases the hit-box of the wire for easier selection."""
        path = QPainterPath()
        path.moveTo(self.line().p1())
        path.lineTo(self.line().p2())

        stroker = QPainterPathStroker()
        stroker.setWidth(10)  # 10px virtual width for mouse detection
        return stroker.createStroke(path)

    def paint(self, painter: QPainter, option, widget: Optional[QWidget] = None) -> None:
        """Draws the wire with dynamic state (selection/glow)."""
        if self.isSelected():
            # Selection uses a brighter/thicker version of the wire's own color
            select_color = QColor(self._color)
            # Brighten the color for selection visibility
            h, s, l, a = select_color.getHsl()
            select_color.setHsl(h, s, min(l + 40, 255), a)
            pen = QPen(select_color, 3)
            pen.setCosmetic(True)
        elif self.is_highlighted:
            # Glow uses the wire's own color with transparency
            glow_color = QColor(self._color)
            glow_color.setAlpha(140)
            pen = QPen(glow_color, 6)
            pen.setCosmetic(True)
        else:
            pen = self.pen()

        painter.setPen(pen)
        painter.drawLine(self.line())

    def set_glow(self, enabled: bool) -> None:
        """Triggers a visual highlight of the segment."""
        if self.is_highlighted != enabled:
            self.is_highlighted = enabled
            self.update()

    def hoverEnterEvent(self, event) -> None:
        if not self.preview and self.net_id is not None:
            view = self.scene().views()[0]
            for wire in view.net_to_wires.get(self.net_id, []):
                wire.set_glow(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        if not self.preview and self.net_id is not None:
            view = self.scene().views()[0]
            for wire in view.net_to_wires.get(self.net_id, []):
                wire.set_glow(False)
        super().hoverLeaveEvent(event)