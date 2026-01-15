from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsItem
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker
from PySide6.QtCore import Qt


class WireSegmentItem(QGraphicsLineItem):
    def __init__(self, x1, y1, x2, y2, net_id=None, preview=False):
        super().__init__(x1, y1, x2, y2)

        # FIX: Assign the passed net_id
        self.net_id = net_id
        self.preview = preview
        self.is_highlighted = False

        # Selection Setup
        if not self.preview:
            # ItemIsSelectable allows the item to be part of scene.selectedItems()
            self.setFlags(QGraphicsItem.ItemIsSelectable)
            # FIX: Must allow LeftButton for selection to work
            self.setAcceptedMouseButtons(Qt.LeftButton)

        self.base_pen = QPen(QColor(255, 0, 0), 2)  # Changed to black for standard wires
        self.base_pen.setCosmetic(True)
        self.base_pen.setCapStyle(Qt.RoundCap)
        self.base_pen.setJoinStyle(Qt.RoundJoin)

        if preview:
            self.base_pen.setColor(QColor(255, 0, 0))
            self.base_pen.setStyle(Qt.CustomDashLine)
            self.base_pen.setDashPattern([4, 4])

        self.setPen(self.base_pen)
        self.setAcceptHoverEvents(True)
        self.setZValue(0.4)

    def shape(self):
        """Creates a thicker 'invisible' area around the wire to make it easier to click."""
        path = QPainterPath()
        path.moveTo(self.line().p1())
        path.lineTo(self.line().p2())

        stroker = QPainterPathStroker()
        stroker.setWidth(10)  # Clickable area is 10px wide
        stroker.setCapStyle(Qt.RoundCap)
        return stroker.createStroke(path)

    def paint(self, painter, option, widget):
        """Override paint to handle the selection highlight."""
        # Use a bright blue for selection
        if self.isSelected():
            selection_pen = QPen(QColor(0, 120, 215), 3)
            selection_pen.setCosmetic(True)
            painter.setPen(selection_pen)
        elif self.is_highlighted:
            glow_pen = QPen(QColor(220, 50, 50, 110), 6)
            glow_pen.setCosmetic(True)
            painter.setPen(glow_pen)
        else:
            painter.setPen(self.pen())

        painter.drawLine(self.line())

    def set_glow(self, enabled: bool):
        if enabled == self.is_highlighted:
            return
        self.is_highlighted = enabled
        self.update()  # Trigger a repaint to show/hide the glow

    def hoverEnterEvent(self, event):
        if self.preview: return
        view = self.scene().views()[0]
        if self.net_id is not None:
            # Highlighting the whole net
            for wire in view.net_to_wires.get(self.net_id, []):
                wire.set_glow(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if self.preview: return
        view = self.scene().views()[0]
        if self.net_id is not None:
            for wire in view.net_to_wires.get(self.net_id, []):
                wire.set_glow(False)
        super().hoverLeaveEvent(event)