from PySide6.QtWidgets import QGraphicsLineItem
from PySide6.QtGui import QPen, QColor
from PySide6.QtCore import Qt


class WireSegmentItem(QGraphicsLineItem):
    def __init__(self, x1, y1, x2, y2, net_id=None, preview=False):
        super().__init__(x1, y1, x2, y2)

        self.net_id = None
        self.is_highlighted = False

        self.base_pen = QPen(QColor(255, 0, 0), 2)
        self.base_pen.setCosmetic(True)
        self.base_pen.setCapStyle(Qt.RoundCap)
        self.base_pen.setJoinStyle(Qt.RoundJoin)

        if preview:
            self.base_pen.setStyle(Qt.CustomDashLine)
            self.base_pen.setDashPattern([4, 4])

        self.setPen(self.base_pen)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.setZValue(0.4)

    def set_glow(self, enabled: bool):
        if enabled == self.is_highlighted:
            return

        self.is_highlighted = enabled

        if enabled:
            glow_pen = QPen(QColor(220, 50, 50, 110), 6)
            glow_pen.setCosmetic(True)
            glow_pen.setCapStyle(Qt.RoundCap)
            glow_pen.setJoinStyle(Qt.RoundJoin)
            self.setPen(glow_pen)
        else:
            self.setPen(self.base_pen)

    def hoverEnterEvent(self, event):
        view = self.scene().views()[0]
        net_id = self.net_id

        if net_id is not None:
            for wire in view.net_to_wires.get(net_id, []):
                wire.set_glow(True)

        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        view = self.scene().views()[0]
        net_id = self.net_id

        if net_id is not None:
            for wire in view.net_to_wires.get(net_id, []):
                wire.set_glow(False)

        super().hoverLeaveEvent(event)

