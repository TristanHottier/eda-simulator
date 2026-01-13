from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QColor


class SchematicView(QGraphicsView):
    def __init__(self):
        super().__init__()

        # Scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setSceneRect(-5000, -5000, 10000, 10000)  # modest scene for components

        # Zoom & pan
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.zoom_step = 1.2

        # Smooth rendering
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)

    def wheelEvent(self, event):
        """Zoom in/out with mouse wheel"""
        factor = self.zoom_step if event.angleDelta().y() > 0 else 1 / self.zoom_step
        self.scale(factor, factor)

    def drawBackground(self, painter: QPainter, rect):
        """Draw a uniform, infinite grid based on the visible rect"""
        grid_size = 50  # distance between grid lines in scene units
        color = QColor(180, 180, 180)  # uniform gray

        # Determine start points aligned to the grid
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)
        right = int(rect.right())
        bottom = int(rect.bottom())

        # Set pen once for all lines
        pen = QPen(color)
        pen.setWidth(0)  # cosmetic line (1-pixel regardless of zoom)
        painter.setPen(pen)

        # Draw vertical lines
        x = left
        while x <= right:
            painter.drawLine(x, top, x, bottom)
            x += grid_size

        # Draw horizontal lines
        y = top
        while y <= bottom:
            painter.drawLine(left, y, right, y)
            y += grid_size
