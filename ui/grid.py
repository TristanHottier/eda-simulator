# ui/grid.py
from typing import Optional
from PySide6.QtWidgets import QGraphicsItem, QWidget
from PySide6.QtGui import QPen, QColor, QPainter
from PySide6.QtCore import QRectF, Qt


class GridItem(QGraphicsItem):
    """
    A background item that draws a coordinate grid.
    Static and non-selectable to serve as a visual guide for component snapping.
    """

    def __init__(self, spacing: int = 50):
        super().__init__()
        self.spacing = spacing

        # Ensure the grid is behind all other elements
        self.setZValue(-100)

        # Disable caching to prevent distortion/smearing during panning.
        # Instead, we optimize the paint method to draw only visible lines.
        self.setCacheMode(QGraphicsItem.NoCache)
        self.setFlag(QGraphicsItem.ItemHasNoContents, False)

    def boundingRect(self) -> QRectF:
        """Defines the area that the grid covers."""
        return QRectF(-5000, -5000, 10000, 10000)

    def paint(self, painter: QPainter, option, widget: Optional[QWidget] = None) -> None:
        """Draws the vertical and horizontal grid lines within the visible area."""
        # Setup a sharp, non-antialiased cosmetic pen
        pen = QPen(QColor(210, 210, 210), 0)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing, False)

        # Optimization: Only draw the portion of the grid currently visible in the viewport
        visible_rect = option.exposedRect

        left = int(visible_rect.left()) - (int(visible_rect.left()) % self.spacing)
        top = int(visible_rect.top()) - (int(visible_rect.top()) % self.spacing)
        right = int(visible_rect.right())
        bottom = int(visible_rect.bottom())

        # Draw vertical lines
        for x in range(left, right + 5 * self.spacing, 5 * self.spacing):
            painter.drawLine(x, top, x, bottom)

        # Draw horizontal lines
        for y in range(top, bottom + 5 * self.spacing, 5 * self.spacing):
            painter.drawLine(left, y, right, y)