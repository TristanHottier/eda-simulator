from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Qt
from ui.schematic_view import SchematicView
from app.component_palette import ComponentPalette


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EDA Simulator — Phase 1")

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout()
        central.setLayout(main_layout)

        # --- Schematic view ---
        self.schematic_view = SchematicView()
        main_layout.addWidget(self.schematic_view, 1)

        # --- Right-side panel (only palette now) ---
        side_panel = QVBoxLayout()
        main_layout.addLayout(side_panel)

        self.palette = ComponentPalette(self.schematic_view)
        side_panel.addWidget(self.palette)

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_Z:
                if hasattr(self.schematic_view, "undo_stack"):
                    self.schematic_view.undo_stack.undo()
            elif event.key() == Qt.Key_Y:
                if hasattr(self.schematic_view, "undo_stack"):
                    self.schematic_view.undo_stack.redo()
            elif event.key() == Qt.Key_S:  # Add Save Shortcut
                self.schematic_view.save_to_json()
            elif event.key() == Qt.Key_O:  # Add Open Shortcut
                self.schematic_view.load_from_json()
        else:
            super().keyPressEvent(event)

