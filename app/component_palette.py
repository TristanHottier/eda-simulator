from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame
from PySide6.QtCore import Qt


class ComponentPalette(QWidget):
    def __init__(self, schematic_view):
        super().__init__()
        self.schematic_view = schematic_view

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tool section
        layout.addWidget(QLabel("Tools"))
        self.select_tool_btn = QPushButton("Select/Move")
        self.wire_tool_btn = QPushButton("Wire Tool")
        layout.addWidget(self.select_tool_btn)
        layout.addWidget(self.wire_tool_btn)

        self.select_tool_btn.setCheckable(True)
        self.wire_tool_btn.setCheckable(True)
        self.select_tool_btn.setChecked(True)

        # Connect buttons
        self.select_tool_btn.clicked.connect(self.activate_select_tool)
        self.wire_tool_btn.clicked.connect(self.activate_wire_tool)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        # Component section
        layout.addWidget(QLabel("Components"))
        for comp_type in ["Resistor", "Capacitor", "LED"]:
            btn = QPushButton(comp_type)
            layout.addWidget(btn)
            btn.clicked.connect(lambda checked, c=comp_type: self.add_component(c))

        # --------------------------
        # Tool functions
        # --------------------------

    def activate_select_tool(self):
        self.select_tool_btn.setChecked(True)
        self.wire_tool_btn.setChecked(False)
        self.schematic_view.select_tool_active = True
        self.schematic_view.wire_tool_active = False
        self.schematic_view.setCursor(Qt.ArrowCursor)
        self.schematic_view.mode = "component"

    def activate_wire_tool(self):
        self.select_tool_btn.setChecked(False)
        self.wire_tool_btn.setChecked(True)
        self.schematic_view.select_tool_active = False
        self.schematic_view.wire_tool_active = True
        self.schematic_view.setCursor(Qt.CrossCursor)
        self.schematic_view.drawing_wire = False  # reset in case leftover
        self.schematic_view.mode = "wire"

        # --------------------------
        # Component placement
        # --------------------------

    def add_component(self, comp_type):
        ref = f"{comp_type[0]}{len(self.schematic_view.components) + 1}"
        self.schematic_view.add_component(ref, comp_type)
