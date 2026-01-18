# app_window.py
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QPushButton
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

        # --- Theme State ---
        self._dark_mode = True  # Start in dark mode

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

        # 0. Theme Toggle Button (Top of panel)
        self.theme_toggle_btn = QPushButton("☀")  # Sun icon for switching to light mode
        self.theme_toggle_btn.setFixedSize(32, 32)
        self.theme_toggle_btn.setToolTip("Switch to Light Mode")
        self.theme_toggle_btn.clicked.connect(self._toggle_theme)

        # Create a horizontal layout to right-align the button
        theme_layout = QHBoxLayout()
        theme_layout.addStretch()
        theme_layout.addWidget(self.theme_toggle_btn)
        side_panel_layout.addLayout(theme_layout)

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

        # Apply initial dark theme
        self._apply_theme()

    def _toggle_theme(self) -> None:
        """Toggles between light and dark mode."""
        self._dark_mode = not self._dark_mode
        self._apply_theme()

        # Update button icon and tooltip
        if self._dark_mode:
            self.theme_toggle_btn.setText("☀")  # Sun = click to go light
            self.theme_toggle_btn.setToolTip("Switch to Light Mode")
        else:
            self.theme_toggle_btn.setText("🌙")  # Moon = click to go dark
            self.theme_toggle_btn.setToolTip("Switch to Dark Mode")

    def _apply_theme(self) -> None:
        """Applies the current theme to all components."""
        # Update schematic view
        self.schematic_view.set_dark_mode(self._dark_mode)

        # Update all existing components in the scene
        from ui.component_item import ComponentItem
        for item in self.schematic_view.scene().items():
            if isinstance(item, ComponentItem):
                item.set_dark_mode(self._dark_mode)

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