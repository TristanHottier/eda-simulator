from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPen, QColor, QPainter
from PySide6.QtCore import QRectF, Qt


class GridItem(QGraphicsItem):
    def __init__(self, spacing=50):
        super().__init__()
        self.spacing = spacing

    def boundingRect(self) -> QRectF:
        return QRectF(-5000, -5000, 10000, 10000)

    def paint(self, painter: 'QPainter', option, widget=None):
        painter.setPen(QPen(QColor(200, 200, 200), 0))
        left, top, width, height = self.boundingRect().getRect()
        # Draw vertical lines
        x = left
        while x <= left + width:
            painter.drawLine(x, top, x, top + height)
            x += self.spacing
        # Draw horizontal lines
        y = top
        while y <= top + height:
            painter.drawLine(left, y, left + width, y)
            y += self.spacing
