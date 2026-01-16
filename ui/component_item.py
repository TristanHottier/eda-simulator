# ui/component_item.py
from typing import Optional, Any, List
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QBrush, QColor
from ui.undo_commands import MoveComponentCommand, RotateComponentCommand
from ui.pin_item import PinItem  # Ensure PinItem is imported


class ComponentItem(QGraphicsRectItem):
    GRID_SIZE = 50
    UNIT_MAP = {"resistance": "Ω", "capacitance": "nF", "voltage_drop": "V"}

    def __init__(self, component_model, width: int = 100, height: int = 50):
        super().__init__(0, 0, width, height)
        self.model = component_model
        self.ref: str = self.model.ref
        self.old_pos: Optional[QPointF] = None

        # --- Flags ---
        self.setFlags(
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsFocusable |
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemSendsScenePositionChanges |
            QGraphicsItem.ItemSendsGeometryChanges
        )

        # Set origin to center for clean rotation
        self.setTransformOriginPoint(width / 2, height / 2)
        self.setAcceptedMouseButtons(Qt.LeftButton)

        # --- Visuals ---
        self.setBrush(QBrush(QColor("#ffeeaa")))
        self.setPen(QColor("black"))

        # --- Label ---
        self.label = QGraphicsTextItem("", self)
        self.refresh_label()

        # --- FIX: Restore Pins ---
        # Iterate through the logic model's pins and create visual PinItems
        self.pin_items: List[PinItem] = []
        for pin_logic in self.model.pins:
            # pin_logic provides rel_x and rel_y (offsets from component origin)
            p_item = PinItem(pin_logic, pin_logic.rel_x, pin_logic.rel_y, self)
            self.pin_items.append(p_item)

    def refresh_label(self) -> None:
        """Updates the text label based on current model parameters."""
        main_key = next(
            (k for k in self.UNIT_MAP.keys() if k in self.model.parameters),
            None
        )

        if main_key:
            val = self.model.parameters[main_key]
            unit = self.UNIT_MAP.get(main_key, "")
            text = f"{self.ref} {val}{unit}"
        else:
            text = self.ref

        self.label.setPlainText(text)
        self.update_label_position()

    def update_label_position(self) -> None:
        """Centers the label above the component."""
        rect = self.rect()
        label_rect = self.label.boundingRect()
        self.label.setPos(
            (rect.width() - label_rect.width()) / 2,
            -label_rect.height() - 5
        )

    def _snap_to_grid(self, pos: QPointF) -> QPointF:
        """Calculates the nearest grid intersection for a given position."""
        x = round(pos.x() / self.GRID_SIZE) * self.GRID_SIZE
        y = round(pos.y() / self.GRID_SIZE) * self.GRID_SIZE
        return QPointF(x, y)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        """Forces the item to snap to the grid in real-time during movement."""
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            return self._snap_to_grid(value)
        return super().itemChange(change, value)

    def mousePressEvent(self, event) -> None:
        self.old_pos = self.scenePos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        # Register movement in undo stack
        new_pos = self.scenePos()
        if self.old_pos and self.old_pos != new_pos:
            view = self.scene().views()[0]
            if hasattr(view, "undo_stack"):
                view.undo_stack.push(MoveComponentCommand(self, self.old_pos, new_pos))

        super().mouseReleaseEvent(event)

    def update_label_after_dialog(self, comp_model) -> None:
        """Public API to trigger a label refresh after model edits."""
        self.model = comp_model
        self.refresh_label()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_R:
            old_rot = self.rotation()
            new_rot = (old_rot + 90) % 360

            view = self.scene().views()[0]
            if hasattr(view, "undo_stack"):
                view.undo_stack.push(RotateComponentCommand(self, old_rot, new_rot))
            else:
                self.setRotation(new_rot)
        else:
            super().keyPressEvent(event)