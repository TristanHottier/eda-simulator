# app/component_palette.py
from typing import TYPE_CHECKING
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame
from PySide6.QtCore import Qt, QPointF
from core.component import Component
from ui.component_item import ComponentItem

if TYPE_CHECKING:
    from ui.schematic_view import SchematicView


class ComponentPalette(QWidget):
    """
    Side panel for selecting tools and adding components to the schematic.
    """

    def __init__(self, schematic_view: 'SchematicView'):
        super().__init__()
        self.schematic_view = schematic_view

        layout = QVBoxLayout()
        self.setLayout(layout)

        # --- Tool Section ---
        layout.addWidget(QLabel("<b>Tools</b>"))
        self.select_tool_btn = QPushButton("Select/Move")
        self.wire_tool_btn = QPushButton("Wire Tool")

        for btn in [self.select_tool_btn, self.wire_tool_btn]:
            btn.setCheckable(True)
            layout.addWidget(btn)

        self.select_tool_btn.setChecked(True)
        self.select_tool_btn.clicked.connect(lambda: self._set_tool_mode("component"))
        self.wire_tool_btn.clicked.connect(lambda: self._set_tool_mode("wire"))

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # --- Component Section ---
        layout.addWidget(QLabel("<b>Components</b>"))
        component_types = ["Resistor", "Capacitor", "LED"]
        for comp_type in component_types:
            btn = QPushButton(comp_type)
            # Use default argument in lambda to capture the current string value
            btn.clicked.connect(lambda checked, t=comp_type: self.add_component(t))
            layout.addWidget(btn)

        layout.addStretch()

    def _set_tool_mode(self, mode: str) -> None:
        """Synchronizes UI buttons and SchematicView state."""
        self.schematic_view.mode = mode

        # Update Button states
        self.select_tool_btn.setChecked(mode == "component")
        self.wire_tool_btn.setChecked(mode == "wire")

        # Update Cursor
        cursor = Qt.ArrowCursor if mode == "component" else Qt.CrossCursor
        self.schematic_view.setCursor(cursor)

        # Reset wire tool state if switching away
        if mode != "wire":
            self.schematic_view.drawing_wire = False

    def add_component(self, comp_type: str) -> None:
        """Instantiates a new component at the center of the current view."""
        # Create logical model
        ref_prefix = comp_type[0].upper()
        existing_count = sum(1 for c in self.schematic_view.components if c.type == comp_type.lower())
        ref_designator = f"{ref_prefix}{existing_count + 1}"

        model = Component(ref=ref_designator, comp_type=comp_type.lower())
        self.schematic_view.components.append(model)

        # Create visual item
        item = ComponentItem(model)

        # Place in center of visible area, snapped to grid
        view_center = self.schematic_view.mapToScene(self.schematic_view.viewport().rect().center())
        snapped_x = round(view_center.x() / 50) * 50
        snapped_y = round(view_center.y() / 50) * 50

        item.setPos(QPointF(snapped_x, snapped_y))
        self.schematic_view.scene().addItem(item)