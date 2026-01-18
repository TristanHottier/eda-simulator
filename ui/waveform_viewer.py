# ui/waveform_viewer.py
"""
Waveform Viewer — PyQtGraph-based plot widget for simulation results.

This module provides a waveform viewer for displaying simulation
results including transient, AC, and DC sweep analyses.
"""

from typing import Dict, List, Optional, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QScrollArea, QFrame, QSplitter,
    QGroupBox, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

# Try to import pyqtgraph, provide fallback if not available
try: 
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError: 
    PYQTGRAPH_AVAILABLE = False

from simulation.waveform_data import (
    Waveform, WaveformGroup, WaveformType, AxisType,
    SimulationData, OperatingPointData,
    get_waveform_color, WAVEFORM_COLORS
)


class WaveformPlot(QWidget):
    """
    A single plot widget for displaying waveforms.

    Uses PyQtGraph for high-performance rendering.
    """

    # Signal emitted when cursor position changes
    cursor_moved = Signal(float, float)  # x, y

    def __init__(self, title: str = "", x_label: str = "", y_label: str = "", parent=None):
        super().__init__(parent)

        self._title = title
        self._x_label = x_label
        self._y_label = y_label
        self._waveforms: Dict[str, Tuple[Waveform, object]] = {}  # name -> (waveform, plot_item)
        self._dark_mode = True

        self._setup_ui()

    def _setup_ui(self):
        """Sets up the plot widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if PYQTGRAPH_AVAILABLE: 
            self._setup_pyqtgraph()
        else: 
            self._setup_fallback()

    def _setup_pyqtgraph(self):
        """Sets up the PyQtGraph plot widget."""
        # Configure PyQtGraph
        pg.setConfigOptions(antialias=True)

        # Create plot widget
        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setBackground('#1e1e1e')
        self._plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Set labels
        self._plot_widget.setTitle(self._title, color='w', size='12pt')
        self._plot_widget.setLabel('bottom', self._x_label, color='w')
        self._plot_widget.setLabel('left', self._y_label, color='w')

        # Enable mouse interaction
        self._plot_widget.setMouseEnabled(x=True, y=True)
        self._plot_widget.enableAutoRange()

        # Add crosshair cursor
        self._vline = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('y', width=1, style=Qt.DashLine))
        self._hline = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('y', width=1, style=Qt.DashLine))
        self._plot_widget.addItem(self._vline, ignoreBounds=True)
        self._plot_widget.addItem(self._hline, ignoreBounds=True)
        self._vline.hide()
        self._hline.hide()

        # Connect mouse move
        self._plot_widget.scene().sigMouseMoved.connect(self._on_mouse_moved)

        # Add legend
        self._legend = self._plot_widget.addLegend(offset=(10, 10))

        self.layout().addWidget(self._plot_widget)

    def _setup_fallback(self):
        """Sets up a fallback widget when PyQtGraph is not available."""
        fallback_label = QLabel(
            "PyQtGraph not installed.\n\n"
            "Install it with:\n"
            "pip install pyqtgraph"
        )
        fallback_label.setAlignment(Qt.AlignCenter)
        fallback_label.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 20px;
                font-size: 14px;
            }
        """)
        self.layout().addWidget(fallback_label)

    def _on_mouse_moved(self, pos):
        """Handles mouse movement for crosshair cursor."""
        if not PYQTGRAPH_AVAILABLE: 
            return

        if self._plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self._plot_widget.getPlotItem().vb.mapSceneToView(pos)
            x, y = mouse_point.x(), mouse_point.y()

            self._vline.setPos(x)
            self._hline.setPos(y)
            self._vline.show()
            self._hline.show()

            self.cursor_moved.emit(x, y)
        else:
            self._vline.hide()
            self._hline.hide()

    def add_waveform(self, waveform: Waveform, color: Optional[str] = None) -> bool:
        """
        Adds a waveform to the plot.

        Args:
            waveform: The waveform to add.
            color: Optional color override (hex string).

        Returns: 
            bool: True if successfully added.
        """
        if not PYQTGRAPH_AVAILABLE: 
            return False

        if waveform.name in self._waveforms:
            self.remove_waveform(waveform.name)

        # Determine color
        if color is None: 
            color = waveform.color or get_waveform_color(len(self._waveforms))

        # Create pen
        pen = pg.mkPen(color=color, width=2)

        # Add plot
        plot_item = self._plot_widget.plot(
            waveform.x_data,
            waveform.y_data,
            pen=pen,
            name=waveform.name
        )

        self._waveforms[waveform.name] = (waveform, plot_item)
        return True

    def remove_waveform(self, name: str) -> bool:
        """
        Removes a waveform from the plot.

        Args:
            name: Name of the waveform to remove.

        Returns:
            bool: True if successfully removed.
        """
        if not PYQTGRAPH_AVAILABLE: 
            return False

        if name in self._waveforms:
            waveform, plot_item = self._waveforms[name]
            self._plot_widget.removeItem(plot_item)
            del self._waveforms[name]
            return True
        return False

    def clear_all(self):
        """Removes all waveforms from the plot."""
        if not PYQTGRAPH_AVAILABLE:
            return

        for name in list(self._waveforms.keys()):
            self.remove_waveform(name)

        self._plot_widget.clear()

        # Re-add crosshairs
        self._plot_widget.addItem(self._vline, ignoreBounds=True)
        self._plot_widget.addItem(self._hline, ignoreBounds=True)

    def set_waveform_visible(self, name:  str, visible: bool):
        """Sets the visibility of a waveform."""
        if not PYQTGRAPH_AVAILABLE:
            return

        if name in self._waveforms:
            waveform, plot_item = self._waveforms[name]
            waveform.visible = visible
            plot_item.setVisible(visible)

    def auto_range(self):
        """Auto-scales the plot to fit all data."""
        if PYQTGRAPH_AVAILABLE: 
            self._plot_widget.autoRange()

    def set_x_range(self, x_min: float, x_max: float):
        """Sets the X-axis range."""
        if PYQTGRAPH_AVAILABLE:
            self._plot_widget.setXRange(x_min, x_max)

    def set_y_range(self, y_min: float, y_max:  float):
        """Sets the Y-axis range."""
        if PYQTGRAPH_AVAILABLE: 
            self._plot_widget.setYRange(y_min, y_max)

    def set_title(self, title:  str):
        """Sets the plot title."""
        self._title = title
        if PYQTGRAPH_AVAILABLE: 
            self._plot_widget.setTitle(title, color='w', size='12pt')

    def set_labels(self, x_label: str, y_label: str):
        """Sets the axis labels."""
        self._x_label = x_label
        self._y_label = y_label
        if PYQTGRAPH_AVAILABLE:
            self._plot_widget.setLabel('bottom', x_label, color='w')
            self._plot_widget.setLabel('left', y_label, color='w')

    def set_dark_mode(self, dark:  bool):
        """Sets the color scheme."""
        self._dark_mode = dark
        if not PYQTGRAPH_AVAILABLE: 
            return

        if dark:
            self._plot_widget.setBackground('#1e1e1e')
            text_color = 'w'
            grid_alpha = 0.3
        else: 
            self._plot_widget.setBackground('#ffffff')
            text_color = 'k'
            grid_alpha = 0.2

        self._plot_widget.setTitle(self._title, color=text_color, size='12pt')
        self._plot_widget.setLabel('bottom', self._x_label, color=text_color)
        self._plot_widget.setLabel('left', self._y_label, color=text_color)
        self._plot_widget.showGrid(x=True, y=True, alpha=grid_alpha)

    def get_waveform_names(self) -> List[str]:
        """Returns the names of all waveforms in the plot."""
        return list(self._waveforms.keys())

    def export_image(self, filename:  str):
        """Exports the plot as an image."""
        if PYQTGRAPH_AVAILABLE: 
            exporter = pg.exporters.ImageExporter(self._plot_widget.getPlotItem())
            exporter.export(filename)


class WaveformLegendItem(QWidget):
    """A single item in the waveform legend with visibility toggle."""

    visibility_changed = Signal(str, bool)  # name, visible

    def __init__(self, name: str, color: str, parent=None):
        super().__init__(parent)
        self._name = name
        self._color = color

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(5)

        # Visibility checkbox
        self._checkbox = QCheckBox()
        self._checkbox.setChecked(True)
        self._checkbox.stateChanged.connect(self._on_visibility_changed)
        layout.addWidget(self._checkbox)

        # Color swatch
        self._swatch = QFrame()
        self._swatch.setFixedSize(16, 16)
        self._swatch.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
        layout.addWidget(self._swatch)

        # Name label
        self._label = QLabel(name)
        self._label.setStyleSheet("color: white;")
        layout.addWidget(self._label)

        layout.addStretch()

    def _on_visibility_changed(self, state):
        """Handles visibility checkbox state change."""
        self.visibility_changed.emit(self._name, state == Qt.Checked)

    def set_visible(self, visible:  bool):
        """Sets the visibility state."""
        self._checkbox.setChecked(visible)

    def set_dark_mode(self, dark: bool):
        """Updates colors for theme."""
        text_color = "white" if dark else "black"
        self._label.setStyleSheet(f"color: {text_color};")


class CursorReadout(QWidget):
    """Displays cursor position and waveform values."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        self._x_label = QLabel("X:  ---")
        self._x_label.setStyleSheet("color: white; font-family: monospace;")
        layout.addWidget(self._x_label)

        layout.addSpacing(20)

        self._y_label = QLabel("Y: ---")
        self._y_label.setStyleSheet("color:  white; font-family: monospace;")
        layout.addWidget(self._y_label)

        layout.addStretch()

    def update_position(self, x: float, y: float):
        """Updates the displayed cursor position."""
        self._x_label.setText(f"X: {self._format_value(x)}")
        self._y_label.setText(f"Y: {self._format_value(y)}")

    def _format_value(self, value: float) -> str:
        """Formats a value with appropriate precision."""
        if abs(value) < 1e-9:
            return f"{value * 1e12:.3f} p"
        elif abs(value) < 1e-6:
            return f"{value * 1e9:.3f} n"
        elif abs(value) < 1e-3:
            return f"{value * 1e6:.3f} µ"
        elif abs(value) < 1:
            return f"{value * 1e3:.3f} m"
        elif abs(value) < 1e3:
            return f"{value:.3f}"
        elif abs(value) < 1e6:
            return f"{value / 1e3:.3f} k"
        else:
            return f"{value / 1e6:.3f} M"

    def set_dark_mode(self, dark: bool):
        """Updates colors for theme."""
        text_color = "white" if dark else "black"
        self._x_label.setStyleSheet(f"color: {text_color}; font-family:  monospace;")
        self._y_label.setStyleSheet(f"color:  {text_color}; font-family:  monospace;")


class OperatingPointPanel(QWidget):
    """Displays DC operating point results in a table-like format."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title = QLabel("DC Operating Point")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: white;")
        layout.addWidget(title)

        # Scroll area for values
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border:  none; }")

        self._content = QWidget()
        self._content_layout = QGridLayout(self._content)
        self._content_layout.setColumnStretch(1, 1)
        scroll.setWidget(self._content)

        layout.addWidget(scroll)

        self._dark_mode = True

    def set_data(self, op_data: OperatingPointData):
        """Sets the operating point data to display."""
        # Clear existing content
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        row = 0
        text_color = "white" if self._dark_mode else "black"

        # Node voltages section
        if op_data.node_voltages: 
            header = QLabel("Node Voltages")
            header.setStyleSheet(f"font-weight: bold; color: {text_color};")
            self._content_layout.addWidget(header, row, 0, 1, 2)
            row += 1

            for node, voltage in sorted(op_data.node_voltages.items()):
                name_label = QLabel(f"V({node}):")
                name_label.setStyleSheet(f"color:  {text_color};")
                value_label = QLabel(f"{voltage:.6g} V")
                value_label.setStyleSheet(f"color: #4ECDC4; font-family: monospace;")

                self._content_layout.addWidget(name_label, row, 0)
                self._content_layout.addWidget(value_label, row, 1)
                row += 1

        # Branch currents section
        if op_data.branch_currents: 
            spacer = QLabel("")
            self._content_layout.addWidget(spacer, row, 0)
            row += 1

            header = QLabel("Branch Currents")
            header.setStyleSheet(f"font-weight: bold; color: {text_color};")
            self._content_layout.addWidget(header, row, 0, 1, 2)
            row += 1

            for comp, current in sorted(op_data.branch_currents.items()):
                name_label = QLabel(f"I({comp}):")
                name_label.setStyleSheet(f"color: {text_color};")
                value_label = QLabel(f"{current:.6g} A")
                value_label.setStyleSheet(f"color:  #FF6B6B; font-family: monospace;")

                self._content_layout.addWidget(name_label, row, 0)
                self._content_layout.addWidget(value_label, row, 1)
                row += 1

        # Add stretch at bottom
        self._content_layout.setRowStretch(row, 1)

    def clear(self):
        """Clears the display."""
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def set_dark_mode(self, dark: bool):
        """Updates colors for theme."""
        self._dark_mode = dark
        bg_color = "#2d2d2d" if dark else "#f5f5f5"
        self.setStyleSheet(f"background-color:  {bg_color};")


class WaveformViewer(QWidget):
    """
    Main waveform viewer widget.

    Provides a complete interface for viewing simulation results
    including waveform plots, legends, and cursor readouts.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._simulation_data:  Optional[SimulationData] = None
        self._dark_mode = True
        self._current_analysis = None

        self._setup_ui()

    def _setup_ui(self):
        """Sets up the viewer UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main content area with splitter
        self._splitter = QSplitter(Qt.Horizontal)

        # Left side: Plot area
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(5, 5, 5, 5)

        # Cursor readout
        self._cursor_readout = CursorReadout()
        plot_layout.addWidget(self._cursor_readout)

        # Waveform plot (create BEFORE toolbar)
        self._plot = WaveformPlot(
            title="Simulation Results",
            x_label="Time (s)",
            y_label="Voltage (V)"
        )
        self._plot.cursor_moved.connect(self._cursor_readout.update_position)
        plot_layout.addWidget(self._plot, stretch=1)

        self._splitter.addWidget(plot_container)

        # Right side:  Control panel
        control_panel = self._create_control_panel()
        self._splitter.addWidget(control_panel)

        # Set initial splitter sizes (70% plot, 30% controls)
        self._splitter.setSizes([700, 300])

        # Toolbar (create AFTER plot)
        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)

        main_layout.addWidget(self._splitter, stretch=1)

        # Apply initial theme
        self._apply_theme()

    def _create_toolbar(self) -> QWidget:
        """Creates the toolbar widget."""
        toolbar = QWidget()
        toolbar.setFixedHeight(40)
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(5, 5, 5, 5)

        # Analysis selector
        layout.addWidget(QLabel("Analysis:"))
        self._analysis_combo = QComboBox()
        self._analysis_combo.setMinimumWidth(150)
        self._analysis_combo.currentTextChanged.connect(self._on_analysis_changed)
        layout.addWidget(self._analysis_combo)

        layout.addSpacing(20)

        # Auto-range button
        auto_range_btn = QPushButton("Auto Range")
        auto_range_btn.clicked.connect(self._plot.auto_range)
        layout.addWidget(auto_range_btn)

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear)
        layout.addWidget(clear_btn)

        layout.addStretch()

        # Export button
        export_btn = QPushButton("Export...")
        export_btn.clicked.connect(self._on_export)
        layout.addWidget(export_btn)

        return toolbar

    def _create_control_panel(self) -> QWidget:
        """Creates the right-side control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # Waveform legend
        legend_group = QGroupBox("Waveforms")
        legend_layout = QVBoxLayout(legend_group)

        self._legend_scroll = QScrollArea()
        self._legend_scroll.setWidgetResizable(True)
        self._legend_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._legend_content = QWidget()
        self._legend_layout = QVBoxLayout(self._legend_content)
        self._legend_layout.setAlignment(Qt.AlignTop)
        self._legend_scroll.setWidget(self._legend_content)

        legend_layout.addWidget(self._legend_scroll)
        layout.addWidget(legend_group)

        # Operating point panel (shown for OP analysis)
        self._op_panel = OperatingPointPanel()
        self._op_panel.hide()
        layout.addWidget(self._op_panel)

        layout.addStretch()

        return panel

    def set_simulation_data(self, data: SimulationData):
        """
        Sets the simulation data to display.

        Args:
            data: SimulationData containing analysis results.
        """
        print(f"--- VIEWER DEBUG ---")
        if data:
            print(f"Viewer received {len(data.get_available_analyses())} analyses.")
            # Check AC specifically
            if data.ac_analysis:
                print(f"AC Waveforms: {list(data.ac_analysis.waveforms.keys())}")
        else:
            print("Viewer received NULL data!")

        self._simulation_data = data
        self._update_analysis_selector()

        # Auto-select first available analysis
        if self._analysis_combo.count() > 0:
            self._analysis_combo.setCurrentIndex(0)

    def _update_analysis_selector(self):
        """Updates the analysis selector combo box."""
        self._analysis_combo.clear()

        if not self._simulation_data:
            return

        analyses = self._simulation_data.get_available_analyses()

        display_names = {
            "operating_point": "Operating Point",
            "transient": "Transient Analysis",
            "ac_analysis": "AC Analysis",
            "dc_sweep": "DC Sweep"
        }

        for analysis in analyses:
            self._analysis_combo.addItem(display_names.get(analysis, analysis), analysis)

    def _on_analysis_changed(self, text: str):
        """Handles analysis selection change."""
        if not self._simulation_data:
            return

        analysis_type = self._analysis_combo.currentData()
        self._current_analysis = analysis_type

        self._plot.clear_all()
        self._clear_legend()

        if analysis_type == "operating_point":
            self._show_operating_point()
        elif analysis_type == "transient":
            self._show_transient()
        elif analysis_type == "ac_analysis":
            self._show_ac_analysis()
        elif analysis_type == "dc_sweep": 
            self._show_dc_sweep()

    def _show_operating_point(self):
        """Displays operating point results."""
        self._op_panel.show()

        if self._simulation_data and self._simulation_data.operating_point:
            self._op_panel.set_data(self._simulation_data.operating_point)

    def _show_transient(self):
        """Displays transient analysis results."""
        self._op_panel.hide()

        if not self._simulation_data or not self._simulation_data.transient:
            return

        group = self._simulation_data.transient
        self._plot.set_title("Transient Analysis")
        self._plot.set_labels("Time (s)", "Voltage (V)")

        if hasattr(self._plot, '_plot_widget'):
            self._plot._plot_widget.setLogMode(x=False, y=False)

        self._display_waveform_group(group)

    def _show_ac_analysis(self):
        """Displays AC analysis results."""
        self._op_panel.hide()

        if not self._simulation_data or not self._simulation_data.ac_analysis:
            return

        group = self._simulation_data.ac_analysis
        self._plot.set_title("AC Analysis (Frequency Response)")
        self._plot.set_labels("Frequency (Hz)", "Magnitude (V)")

        # --- ADD THIS LINE TO FIX THE GRAPH ---
        if hasattr(self._plot, '_plot_widget'):
            # x=True enables log scale for Frequency, y=False keeps Magnitude linear
            self._plot._plot_widget.setLogMode(x=True, y=False)
        # ---------------------------------------

        self._display_waveform_group(group)

    def _show_dc_sweep(self):
        """Displays DC sweep results."""
        self._op_panel.hide()

        if not self._simulation_data or not self._simulation_data.dc_sweep:
            return

        group = self._simulation_data.dc_sweep
        self._plot.set_title("DC Sweep")
        self._plot.set_labels("Sweep Value (V)", "Voltage (V)")

        self._display_waveform_group(group)

    def _display_waveform_group(self, group: WaveformGroup):
        """Displays all waveforms from a group."""
        for i, (name, waveform) in enumerate(group.waveforms.items()):
            color = waveform.color or get_waveform_color(i)
            # --- DEBUG BLOCK: print data lengths and min/max
            print(f"[DEBUG] {name}: len(x_data)={len(waveform.x_data)}, len(y_data)={len(waveform.y_data)}")
            if hasattr(waveform, 'x_data') and hasattr(waveform, 'y_data') and len(waveform.x_data) and len(
                    waveform.y_data):
                print(
                    f"[DEBUG] {name}: x min={min(waveform.x_data):.2g}, max={max(waveform.x_data):.2g}, y min={min(waveform.y_data):.2g}, max={max(waveform.y_data):.2g}")
            # ---
            self._plot.add_waveform(waveform, color)
            self._add_legend_item(name, color)

        self._plot.auto_range()

    def _add_legend_item(self, name: str, color: str):
        """Adds an item to the legend."""
        item = WaveformLegendItem(name, color)
        item.visibility_changed.connect(self._on_waveform_visibility_changed)
        item.set_dark_mode(self._dark_mode)
        self._legend_layout.addWidget(item)

    def _clear_legend(self):
        """Clears all legend items."""
        while self._legend_layout.count():
            item = self._legend_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_waveform_visibility_changed(self, name: str, visible:  bool):
        """Handles waveform visibility toggle."""
        self._plot.set_waveform_visible(name, visible)

    def _on_export(self):
        """Handles export button click."""
        from PySide6.QtWidgets import QFileDialog

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Waveform",
            "",
            "PNG Image (*.png);;All Files (*)"
        )

        if filename:
            if not filename.endswith('.png'):
                filename += '.png'
            self._plot.export_image(filename)

    def clear(self):
        """Clears all displayed data."""
        self._plot.clear_all()
        self._clear_legend()
        self._op_panel.clear()
        self._simulation_data = None
        self._analysis_combo.clear()

    def set_dark_mode(self, dark: bool):
        """Sets the color scheme."""
        self._dark_mode = dark
        self._apply_theme()

    def _apply_theme(self):
        """Applies the current theme to all components."""
        self._plot.set_dark_mode(self._dark_mode)
        self._cursor_readout.set_dark_mode(self._dark_mode)
        self._op_panel.set_dark_mode(self._dark_mode)

        if self._dark_mode:
            bg_color = "#2d2d2d"
            text_color = "white"
        else:
            bg_color = "#f5f5f5"
            text_color = "black"

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                color: {text_color};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #555555;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox:: title {{
                subcontrol-origin:  margin;
                left: 10px;
                padding: 0 5px;
            }}
            QComboBox, QPushButton {{
                background-color: {'#3d3d3d' if self._dark_mode else '#e0e0e0'};
                border: 1px solid #555555;
                border-radius:  4px;
                padding: 5px 10px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {'#4d4d4d' if self._dark_mode else '#d0d0d0'};
            }}
            QScrollArea {{
                border: none;
            }}
        """)

        # Update legend items
        for i in range(self._legend_layout.count()):
            item = self._legend_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'set_dark_mode'):
                    widget.set_dark_mode(self._dark_mode)

    def add_waveform(self, waveform: Waveform, color: Optional[str] = None):
        """
        Directly adds a waveform to the plot.

        Args:
            waveform: The waveform to add.
            color: Optional color override.
        """
        if color is None:
            color = waveform.color or get_waveform_color(len(self._plot.get_waveform_names()))

        self._plot.add_waveform(waveform, color)
        self._add_legend_item(waveform.name, color)

    def remove_waveform(self, name: str):
        """
        Removes a waveform from the plot.

        Args:
            name: Name of the waveform to remove.
        """
        self._plot.remove_waveform(name)

        # Remove from legend
        for i in range(self._legend_layout.count()):
            item = self._legend_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, '_name') and widget._name == name:
                    widget.deleteLater()
                    break