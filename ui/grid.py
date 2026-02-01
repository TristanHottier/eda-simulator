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
        try:
            self.update()  # Trigger repaint
        except RuntimeError as e:
            pass  # If it ain't broke don't fix it

    def boundingRect(self) -> QRectF:
        MAX = 1e6
        return QRectF(-MAX, -MAX, 2 * MAX, 2 * MAX)

    def paint(self, painter: QPainter, option, widget: Optional[QWidget] = None) -> None:
        """Draws the vertical and horizontal grid lines within the visible area."""
        # Setup a sharp, non-antialiased cosmetic pen
        if self._dark_mode:
            pen = QPen(QColor(60, 60, 60), 0)  # Dark gray lines on dark background
        else:
            pen = QPen(QColor(200, 200, 200), 0)  # Light gray lines on light background

        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing, False)

        # Optimization: Only draw the portion of the grid currently visible in the viewport
        visible_rect = option.exposedRect

        # Calculate the grid alignment based on spacing
        left = int(visible_rect.left())
        if left >= 0:
            left = left - (left % self.spacing)
        else:
            left = left - (self.spacing + (left % self.spacing))

        top = int(visible_rect.top())
        if top >= 0:
            top = top - (top % self.spacing)
        else:
            top = top - (self.spacing + (top % self.spacing))

        right = int(visible_rect.right())
        bottom = int(visible_rect.bottom())

        # Draw vertical lines
        x = left
        while x <= right:
            painter.drawLine(x, top, x, bottom)
            x += 5 * self.spacing

        # Draw horizontal lines
        y = top
        while y <= bottom:
            painter.drawLine(left, y, right, y)
            y += 5 * self.spacing
