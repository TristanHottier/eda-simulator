from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter
from ui.grid import GridItem


class SchematicView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setRenderHints(QPainter.Antialiasing)  # <-- fixed
        self.setDragMode(QGraphicsView.ScrollHandDrag)

        # Scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setSceneRect(QRectF(-5000, -5000, 10000, 10000))

        # Add grid
        grid = GridItem(50)
        self.scene.addItem(grid)

        # Zoom factors
        self.zoom_level = 0
        self.zoom_step = 1.2

    def wheelEvent(self, event):
        """Zoom in/out with mouse wheel"""
        if event.angleDelta().y() > 0:
            factor = self.zoom_step
        else:
            factor = 1 / self.zoom_step
        self.scale(factor, factor)
