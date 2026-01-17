# app_window.py
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame
from PySide6.QtCore import Qt
from ui.schematic_view import SchematicView
from app.component_palette import ComponentPalette
from app.parameter_inspector import ParameterInspector


class AppWindow(QMainWindow):
    """
    The main entry point window for the EDA Simulator.
    Coordinates the Schematic View, Tool Palette, and Parameter Inspector.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EDA Simulator — Phase 1")
        self.resize(1200, 800)

        # --- Central Widget & Main Layout ---
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # --- Schematic View (The Canvas) ---
        self.schematic_view = SchematicView()
        main_layout.addWidget(self.schematic_view, stretch=1)

        # --- Right Side Panel (Tools & Properties) ---
        side_panel_layout = QVBoxLayout()
        main_layout.addLayout(side_panel_layout)

        # 1. Component Palette (Top)
        self.palette = ComponentPalette(self.schematic_view)
        side_panel_layout.addWidget(self.palette)

        # Separator Line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        side_panel_layout.addWidget(line)

        # 2. Parameter Inspector (Bottom)
        self.inspector = ParameterInspector(self.schematic_view)
        side_panel_layout.addWidget(self.inspector)

        # --- Event Connections ---
        # Update inspector whenever the scene selection changes
        self.schematic_view.scene().selectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self) -> None:
        """Syncs the inspector with the currently selected item."""
        from ui.component_item import ComponentItem
        selected = self.schematic_view.scene().selectedItems()

        # If exactly one component is selected, show its parameters
        if len(selected) == 1 and isinstance(selected[0], ComponentItem):
            self.inspector.inspect_component(selected[0])
        else:
            self.inspector.clear_inspector()

    def keyPressEvent(self, event) -> None:
        """Handles global application shortcuts."""
        if event.modifiers() & Qt.ControlModifier:
            key = event.key()
            stack = self.schematic_view.undo_stack

            if key == Qt.Key_Z:
                stack.undo()
            elif key == Qt.Key_Y:
                stack.redo()
            elif key == Qt.Key_S:
                self.schematic_view.save_to_json()
            elif key == Qt.Key_O:
                self.schematic_view.load_from_json()
            elif key == Qt.Key_C:
                self.schematic_view.copy_selection()
            elif key == Qt.Key_V:
                self.schematic_view.paste_selection()
        else:
            super().keyPressEvent(event)