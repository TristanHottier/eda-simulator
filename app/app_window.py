# app_window.py
"""
Main application window for EDA Simulator.

Coordinates the schematic editor, component palette, simulation panel,
and waveform viewer.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame,
    QPushButton, QSplitter, QTabWidget, QLabel
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
        self.setWindowTitle("PyEDA-Sim")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
        )
        self.showFullScreen()

        # --- Title Bar ---
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(32)

        title = QLabel("PyEDA-Sim", self.title_bar)

        self.close_btn = QPushButton("✕", self.title_bar)
        self.close_btn.clicked.connect(self.close)

        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(8, 0, 8, 0)
        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(self.close_btn)

        # --- Theme State ---
        self._dark_mode = True  # Start in dark mode

        # --- Central Widget ---
        central = QWidget()
        self.setCentralWidget(central)

        # ⬇️ CHANGED: vertical layout to host title bar + content
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Add title bar FIRST
        root_layout.addWidget(self.title_bar)

        # --- Main Content Layout (your existing layout) ---
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Main horizontal splitter (schematic | waveform)
        self._main_splitter = QSplitter(Qt.Vertical)

        # --- Top Section: Schematic + Side Panel ---
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(5, 5, 5, 5)

        self.schematic_view = SchematicView()
        top_layout.addWidget(self.schematic_view, stretch=1)

        side_panel = self._create_side_panel()
        top_layout.addWidget(side_panel)

        self._main_splitter.addWidget(top_widget)

        # --- Bottom Section: Waveform Viewer ---
        self.waveform_viewer = WaveformViewer()
        self.waveform_viewer.setMinimumHeight(300)
        self._main_splitter.addWidget(self.waveform_viewer)

        self._main_splitter.setSizes([700, 300])

        main_layout.addWidget(self._main_splitter)

        # Add main content BELOW title bar
        root_layout.addLayout(main_layout)

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

    def _get_theme_colors(self) -> dict:
        """Returns the color palette for the current theme."""
        if self._dark_mode:
            return {
                'bg': '#2d2d2d',
                'text': '#ffffff',
                'panel': '#2d2d2d',
                'button': '#3d3d3d',
                'hover': '#4d4d4d',
                'selected': '#4ECDC4',
                'border': '#555555',
                'scrollbar_bg': '#2d2d2d',
                'scrollbar_handle': '#3d3d3d',
                'scrollbar_handle_hover': '#4d4d4d'
            }
        else:
            return {
                'bg': '#d2d2d2',
                'text': '#000000',
                'panel': '#e1e1e1',
                'button': '#f1f1f1',
                'hover': '#e7e7e7',
                'selected': '#4CAF50',
                'border': '#aaaaaa',
                'scrollbar_bg': 'transparent',
                'scrollbar_handle': '#f1f1f1',
                'scrollbar_handle_hover': '#e7e7e7'
            }

    def _build_theme_stylesheet(self, colors: dict) -> str:
        """Builds the common stylesheet for theme application."""
        return f"""
            QMainWindow, QWidget {{
                background-color: {colors['bg']};
                color: {colors['text']};
            }}
            QTabWidget::pane {{
                background-color: {colors['panel']};
                border: 1px solid {colors['border']};
            }}
            QTabWidget::tab-bar {{
                alignment: left;
            }}
            QTabBar::tab {{
                background-color: {colors['button']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {colors['selected']};
                color: white;
                font-weight: bold;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {colors['hover']};
            }}
            QComboBox, QPushButton {{
                background-color: {colors['button']};
                color: {colors['text']};
            }}
            QPushButton:hover {{
                background-color: {colors['hover']};
            }}
            QPushButton:checked {{
                background-color: {colors['selected']};
                color: white;
            }}
            QScrollBar:vertical {{
                background: {colors['scrollbar_bg']};
                width: 8px;
                margin: 0px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {colors['scrollbar_handle']};
                min-height: 30px;
                border-radius: 4px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {colors['scrollbar_handle_hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}

            QScrollBar:horizontal {{
                background: {colors['scrollbar_bg']};
                height: 8px;
                margin: 0px;
                border: none;
            }}
            QScrollBar::handle:horizontal {{
                background: {colors['scrollbar_handle']};
                min-width: 30px;
                border-radius: 4px;
                margin: 2px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {colors['scrollbar_handle_hover']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
                background: none;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """

    def _apply_theme(self) -> None:
        """Applies the current theme to all components."""
        colors = self._get_theme_colors()
        stylesheet = self._build_theme_stylesheet(colors)

        # Apply to main window
        self.setStyleSheet(stylesheet)
        self.title_bar.setStyleSheet(f"""QWidget {{
                background-color: {colors['bg']};
            }}""")
        self.close_btn.setStyleSheet(f"""QPushButton {{
                background-color: {colors['button']};
                color: {colors['text']};
            }}
            QPushButton:hover {{
                background-color: {'#c42b1c'};
            }}
                    """)

        # Update schematic view
        self.schematic_view.set_dark_mode(self._dark_mode)

        # Update all existing components in the scene
        from ui.component_item import ComponentItem
        for item in self.schematic_view.scene().items():
            if isinstance(item, ComponentItem):
                item.set_dark_mode(self._dark_mode)

        # Update waveform viewer
        self.waveform_viewer.set_dark_mode(self._dark_mode)

        # Update side panels
        for widget in [self.palette, self.simulation_panel, self.inspector]:
            widget.setStyleSheet(stylesheet)

    def _apply_fallback_theme_to_widget(self, widget: QWidget) -> None:
        """Applies theme styling to a widget without set_dark_mode method."""
        colors = self._get_theme_colors()
        widget.setStyleSheet(self._build_theme_stylesheet(colors))

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
