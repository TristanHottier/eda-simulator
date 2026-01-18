# app_window.py
"""
Main application window for EDA Simulator.

Coordinates the schematic editor, component palette, simulation panel,
and waveform viewer.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame,
    QPushButton, QSplitter, QDockWidget, QTabWidget
)
from PySide6.QtCore import Qt
from ui.schematic_view import SchematicView
from app.component_palette import ComponentPalette
from app.parameter_inspector import ParameterInspector
from app.simulation_panel import SimulationPanel
from ui.waveform_viewer import WaveformViewer


class AppWindow(QMainWindow):
    """
    The main entry point window for the EDA Simulator.
    Coordinates the Schematic View, Tool Palette, Parameter Inspector,
    Simulation Panel, and Waveform Viewer.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EDA Simulator — Phase 2")
        self.resize(1400, 900)

        # --- Theme State ---
        self._dark_mode = True  # Start in dark mode

        # --- Central Widget with Splitter ---
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Main horizontal splitter (schematic | waveform)
        self._main_splitter = QSplitter(Qt.Vertical)

        # --- Top Section:  Schematic + Side Panel ---
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(5, 5, 5, 5)

        # Schematic View (The Canvas)
        self.schematic_view = SchematicView()
        top_layout.addWidget(self.schematic_view, stretch=1)

        # Right Side Panel (Tools & Properties)
        side_panel = self._create_side_panel()
        top_layout.addWidget(side_panel)

        self._main_splitter.addWidget(top_widget)

        # --- Bottom Section: Waveform Viewer ---
        self.waveform_viewer = WaveformViewer()
        self.waveform_viewer.setMinimumHeight(150)
        self._main_splitter.addWidget(self.waveform_viewer)

        # Set initial splitter sizes (70% schematic, 30% waveform)
        self._main_splitter.setSizes([600, 300])

        main_layout.addWidget(self._main_splitter)

        # --- Event Connections ---
        self.schematic_view.scene().selectionChanged.connect(self._on_selection_changed)
        self.simulation_panel.simulation_completed.connect(self._on_simulation_completed)

        # Apply initial dark theme
        self._apply_theme()

    def _create_side_panel(self) -> QWidget:
        """Creates the right side panel with tabs."""
        panel = QWidget()
        panel.setFixedWidth(250)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Theme Toggle Button (Top of panel)
        self.theme_toggle_btn = QPushButton("☀")
        self.theme_toggle_btn.setFixedSize(32, 32)
        self.theme_toggle_btn.setToolTip("Switch to Light Mode")
        self.theme_toggle_btn.clicked.connect(self._toggle_theme)

        theme_layout = QHBoxLayout()
        theme_layout.addStretch()
        theme_layout.addWidget(self.theme_toggle_btn)
        layout.addLayout(theme_layout)

        # Tab widget for different panels
        self._tab_widget = QTabWidget()

        # Components Tab
        components_tab = QWidget()
        components_layout = QVBoxLayout(components_tab)
        components_layout.setContentsMargins(5, 5, 5, 5)

        self.palette = ComponentPalette(self.schematic_view)
        components_layout.addWidget(self.palette)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        components_layout.addWidget(line)

        self.inspector = ParameterInspector(self.schematic_view)
        components_layout.addWidget(self.inspector)

        self._tab_widget.addTab(components_tab, "Components")

        # Simulation Tab
        simulation_tab = QWidget()
        simulation_layout = QVBoxLayout(simulation_tab)
        simulation_layout.setContentsMargins(5, 5, 5, 5)

        self.simulation_panel = SimulationPanel(self.schematic_view)
        simulation_layout.addWidget(self.simulation_panel)

        self._tab_widget.addTab(simulation_tab, "Simulate")

        layout.addWidget(self._tab_widget)

        return panel

    def _toggle_theme(self) -> None:
        """Toggles between light and dark mode."""
        self._dark_mode = not self._dark_mode
        self._apply_theme()

        # Update button icon and tooltip
        if self._dark_mode:
            self.theme_toggle_btn.setText("☀")
            self.theme_toggle_btn.setToolTip("Switch to Light Mode")
        else:
            self.theme_toggle_btn.setText("🌙")
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

        # Update waveform viewer
        self.waveform_viewer.set_dark_mode(self._dark_mode)

    def _on_selection_changed(self) -> None:
        """Syncs the inspector with the currently selected item."""
        from ui.component_item import ComponentItem
        selected = self.schematic_view.scene().selectedItems()

        # If exactly one component is selected, show its parameters
        if len(selected) == 1 and isinstance(selected[0], ComponentItem):
            self.inspector.inspect_component(selected[0])
        else:
            self.inspector.clear_inspector()

    def _on_simulation_completed(self, sim_data) -> None:
        """Handles successful simulation completion."""
        self.waveform_viewer.set_simulation_data(sim_data)

        # Switch to show waveform viewer if hidden
        sizes = self._main_splitter.sizes()
        if sizes[1] < 100:
            self._main_splitter.setSizes([600, 300])

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

    def show_waveform_viewer(self):
        """Shows the waveform viewer panel."""
        sizes = self._main_splitter.sizes()
        if sizes[1] < 100:
            self._main_splitter.setSizes([600, 300])

    def hide_waveform_viewer(self):
        """Hides the waveform viewer panel."""
        total = sum(self._main_splitter.sizes())
        self._main_splitter.setSizes([total, 0])
