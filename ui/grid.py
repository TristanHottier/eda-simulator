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
        self._dark_mode = True  # Default to dark mode

        # Ensure the grid is behind all other elements
        self.setZValue(-100)

        # Disable caching to prevent distortion/smearing during panning.
        self.setCacheMode(QGraphicsItem.NoCache)
        self.setFlag(QGraphicsItem.ItemHasNoContents, False)

    def set_dark_mode(self, dark: bool) -> None:
        """Updates the grid color based on theme."""
        self._dark_mode = dark
        self.update()  # Trigger repaint

    def boundingRect(self) -> QRectF:
        """Defines the area that the grid covers."""
        return QRectF(-5000, -5000, 10000, 10000)

    def paint(self, painter: QPainter, option, widget: Optional[QWidget] = None) -> None:
        """Draws the vertical and horizontal grid lines within the visible area."""
        # Setup a sharp, non-antialiased cosmetic pen
        if self._dark_mode:
            pen = QPen(QColor(60, 60, 60), 0)  # Dark gray lines on dark background
        else:
            pen = QPen(QColor(200, 200, 200), 0)  # Light gray lines on light background

        painter.setPen(pen)
        painter.setRenderHint(QPainter. Antialiasing, False)

        # Optimization: Only draw the portion of the grid currently visible in the viewport
        visible_rect = option.exposedRect

        left = int(visible_rect. left()) - (int(visible_rect. left()) % self.spacing)
        top = int(visible_rect.top()) - (int(visible_rect.top()) % self.spacing)
        right = int(visible_rect.right())
        bottom = int(visible_rect. bottom())

        # Draw vertical lines
        for x in range(left, right + 5 * self.spacing, 5 * self.spacing):
            painter.drawLine(x, top, x, bottom)

        # Draw horizontal lines
        for y in range(top, bottom + 5 * self.spacing, 5 * self.spacing):
            painter.drawLine(left, y, right, y)