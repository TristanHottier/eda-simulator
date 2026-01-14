from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from ui.undo_commands import MoveComponentCommand, RotateComponentCommand
from ui.pin_item import PinItem


class ComponentItem(QGraphicsRectItem):
    GRID_SIZE = 50

    def __init__(self, component_model, width=100, height=50):
        super().__init__(0, 0, width, height)
        self.model = component_model
        self.ref = self.model.ref
        self.old_pos = None

        # --- Flags ---
        self.setFlags(
            QGraphicsRectItem.ItemIsSelectable |
            QGraphicsRectItem.ItemIsFocusable |
            QGraphicsRectItem.ItemIsMovable |
            QGraphicsRectItem.ItemSendsScenePositionChanges  # Add this
        )
        # Set origin to center for clean rotation
        self.setTransformOriginPoint(width / 2, height / 2)
        self.setAcceptedMouseButtons(Qt.LeftButton)

        # --- Visuals ---
        self.setBrush(QBrush(QColor("#ffeeaa")))
        self.setPen(QColor("black"))

        # --- Label ---
        self.label = QGraphicsTextItem(self.ref, self)
        self.update_label_position()

        for i, pin in enumerate(self.model.pins):
            # Simple logic: first pin left, second pin right
            x_pos = 0 if i == 0 else width
            y_pos = height / 2
            PinItem(pin, x_pos, y_pos, self)

    def update_label_position(self):
        self.label.setPos(
            (self.rect().width() - self.label.boundingRect().width()) / 2,
            -self.label.boundingRect().height() - 5
        )

    # --- Double-click to open parameter popup ---
    def mouseDoubleClickEvent(self, event):
        view = self.scene().views()[0] if self.scene() and self.scene().views() else None
        if view and getattr(view, "mode", "component") == "wire":
            event.ignore()
            return

        if event.button() == Qt.LeftButton:
            # Lookup model
            comp_model = None
            if view and hasattr(view, "components"):
                comp_model = next((c for c in view.components if c.ref == self.ref), None)

            if comp_model:
                from app.parameter_dialog import ParameterDialog
                dlg = ParameterDialog(self, comp_model, parent=None)
                dlg.exec()  # modal popup
                self.update_label_after_dialog(comp_model)

            event.accept()
            return

        super().mouseDoubleClickEvent(event)

    # --- Snap to grid while moving ---
    def mousePressEvent(self, event):
        view = self.scene().views()[0] if self.scene() and self.scene().views() else None

        if view and getattr(view, "mode", "component") == "wire":
            # In wire mode, do NOT allow moving
            event.ignore()
            return

        # Component mode: call super to enable dragging
        super().mousePressEvent(event)
        self.old_pos = self.pos()

    def mouseMoveEvent(self, event):
        view = self.scene().views()[0] if self.scene() and self.scene().views() else None

        if view and getattr(view, "mode", "component") == "wire":
            # Ignore movement entirely in wire mode
            event.ignore()
            return

        # Component mode: move item normally
        super().mouseMoveEvent(event)

        # Snap to grid
        pos = self.scenePos()
        snapped_x = round(pos.x() / self.GRID_SIZE) * self.GRID_SIZE
        snapped_y = round(pos.y() / self.GRID_SIZE) * self.GRID_SIZE
        self.setPos(snapped_x, snapped_y)

    def mouseReleaseEvent(self, event):
        view = self.scene().views()[0] if self.scene() and self.scene().views() else None

        view = self.scene().views()[0] if self.scene() and self.scene().views() else None
        if view and hasattr(view, "undo_stack") and self.old_pos != self.pos():
            view.undo_stack.push(MoveComponentCommand(self, self.old_pos, self.pos()))

        if not (view and getattr(view, "mode", "component") == "wire"):
            # Snap to grid on release
            pos = self.scenePos()
            snapped_x = round(pos.x() / self.GRID_SIZE) * self.GRID_SIZE
            snapped_y = round(pos.y() / self.GRID_SIZE) * self.GRID_SIZE
            self.setPos(snapped_x, snapped_y)

        super().mouseReleaseEvent(event)

    # --- Update label after editing parameters ---
    def update_label_after_dialog(self, comp_model):
        main_key = next(
            (k for k in ["resistance", "capacitance", "voltage_drop"] if k in comp_model.parameters),
            None
        )
        unit_map = {"resistance": "Ω", "capacitance": "nF", "voltage_drop": "V"}
        if main_key:
            val = comp_model.parameters[main_key]
            unit = unit_map.get(main_key, "")
            self.label.setPlainText(f"{self.ref} {val}{unit}")
        else:
            self.label.setPlainText(self.ref)
        self.update_label_position()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            old_rot = self.rotation()
            new_rot = (old_rot + 90) % 360

            view = self.scene().views()[0] if self.scene().views() else None
            if view and hasattr(view, "undo_stack"):
                view.undo_stack.push(RotateComponentCommand(self, old_rot, new_rot))
            else:
                self.setRotation(new_rot)
            event.accept()
        else:
            super().keyPressEvent(event)
