# app/component_palette.py
from typing import TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QColorDialog
)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor
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
        component_types = ["Resistor", "Capacitor", "LED", "Inductor", "Ground"]
        for comp_type in component_types:
            btn = QPushButton(comp_type)
            # Use default argument in lambda to capture the current string value
            btn.clicked.connect(lambda checked, t=comp_type:  self.add_component(t))
            layout.addWidget(btn)

        # Separator for Sources section
        line_sources = QFrame()
        line_sources.setFrameShape(QFrame.HLine)
        line_sources.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line_sources)

        # --- Sources Section ---
        layout.addWidget(QLabel("<b>Sources</b>"))
        source_types = [
            ("DC Voltage", "dc_voltage_source"),
            ("AC Voltage", "ac_voltage_source"),
            ("DC Current", "dc_current_source")
        ]
        for display_name, comp_type in source_types:
            btn = QPushButton(display_name)
            btn.clicked.connect(lambda checked, t=comp_type: self.add_component(t))
            layout.addWidget(btn)

        # Separator
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)

        # --- Wire Color Section ---
        layout.addWidget(QLabel("<b>Wire Color</b>"))
        self.wire_color_btn = QPushButton("Choose Color...")
        self.wire_color_btn.clicked.connect(self._open_wire_color_dialog)
        layout.addWidget(self.wire_color_btn)

        # Color preview swatch
        self.color_swatch = QFrame()
        self.color_swatch.setFixedHeight(20)
        # Initialize with schematic view's current wire color
        initial_color = self.schematic_view.get_current_wire_color()
        self._current_wire_color = initial_color
        self.color_swatch.setStyleSheet(
            f"background-color: {initial_color.name()}; border: 1px solid #888;"
        )
        layout.addWidget(self.color_swatch)

        # Store current selected color
        self._current_wire_color = QColor(255, 0, 0)

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
        # Determine reference prefix based on component type
        ref_prefixes = {
            "ground": "GND",
            "dc_voltage_source":  "V",
            "ac_voltage_source": "V",
            "dc_current_source": "I"
        }
        ref_prefix = ref_prefixes.get(comp_type.lower(), comp_type[0].upper())

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

    def _open_wire_color_dialog(self) -> None:
        """Opens a color picker dialog and applies the color to selected wires."""
        # Get current color from schematic view
        initial_color = self.schematic_view.get_current_wire_color()

        color = QColorDialog.getColor(
            initial_color,
            self,
            "Select Wire Color"
        )

        if color.isValid():
            self._current_wire_color = color
            # Update the swatch preview
            self.color_swatch.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #888;"
            )
            # Apply to selected wires and set as current color for new wires
            self.schematic_view.set_selected_wire_color_qcolor(color)

    def get_current_wire_color(self) -> QColor:
        """Returns the currently selected wire color."""
        return self._current_wire_color

    def update_color_swatch(self) -> None:
        """Updates the color swatch to match the schematic view's current wire color."""
        color = self.schematic_view.get_current_wire_color()
        self._current_wire_color = color
        self.color_swatch.setStyleSheet(
            f"background-color: {color.name()}; border: 1px solid #888;"
        )
