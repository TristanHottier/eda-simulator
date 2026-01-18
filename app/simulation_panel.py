# app/simulation_panel. py
"""
Simulation Panel — UI controls for running SPICE simulations.

This module provides the simulation control panel with analysis
type selection, parameter configuration, and simulation execution.
"""

from typing import TYPE_CHECKING, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QGroupBox, QFormLayout, QLineEdit, QMessageBox,
    QProgressBar, QFrame
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QDoubleValidator

if TYPE_CHECKING:
    from ui.schematic_view import SchematicView

from simulation.spice_runner import (
    SpiceRunner, AnalysisType, AnalysisConfig,
    SimulationResult, NgspiceNotFoundError, SimulationError
)
from simulation.netlist_generator import (
    NetlistGenerator, MissingGroundError, NetlistError
)
from simulation.waveform_data import SimulationData


class SimulationWorker(QThread):
    """Background worker for running simulations."""

    finished = Signal(object)  # SimulationResult or Exception
    progress = Signal(str)  # Status message

    def __init__(self, netlist: str, config: AnalysisConfig):
        super().__init__()
        self._netlist = netlist
        self._config = config
        self._runner = SpiceRunner()

    def run(self):
        """Runs the simulation in a background thread."""
        try:
            self.progress.emit("Running simulation...")
            result = self._runner.run_simulation(self._netlist, self._config)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(e)


class SimulationPanel(QWidget):
    """
    Panel for configuring and running SPICE simulations.

    Provides controls for:
    - Analysis type selection (OP, Transient, AC, DC Sweep)
    - Analysis parameter configuration
    - Simulation execution
    - Status display
    """

    # Signal emitted when simulation completes successfully
    simulation_completed = Signal(object)  # SimulationData

    def __init__(self, schematic_view: 'SchematicView', parent=None):
        super().__init__(parent)
        self.schematic_view = schematic_view
        self._worker: Optional[SimulationWorker] = None
        self._last_netlist: str = ""

        self._setup_ui()

    def _setup_ui(self):
        """Sets up the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # --- Analysis Selection ---
        layout.addWidget(QLabel("<b>Simulation</b>"))

        analysis_layout = QHBoxLayout()
        analysis_layout.addWidget(QLabel("Analysis: "))

        self._analysis_combo = QComboBox()
        self._analysis_combo.addItem("Operating Point", AnalysisType.OPERATING_POINT)
        self._analysis_combo.addItem("Transient", AnalysisType.TRANSIENT)
        self._analysis_combo.addItem("AC Analysis", AnalysisType.AC_ANALYSIS)
        self._analysis_combo.addItem("DC Sweep", AnalysisType.DC_SWEEP)
        self._analysis_combo.currentIndexChanged.connect(self._on_analysis_changed)
        analysis_layout.addWidget(self._analysis_combo)

        layout.addLayout(analysis_layout)

        # --- Parameter Groups ---
        # Transient parameters
        self._transient_group = self._create_transient_group()
        layout.addWidget(self._transient_group)

        # AC parameters
        self._ac_group = self._create_ac_group()
        layout.addWidget(self._ac_group)

        # DC Sweep parameters
        self._dc_group = self._create_dc_group()
        layout.addWidget(self._dc_group)

        # Hide all parameter groups initially (OP doesn't need params)
        self._transient_group.hide()
        self._ac_group.hide()
        self._dc_group.hide()

        # --- Simulate Button ---
        self._simulate_btn = QPushButton("▶ Simulate")
        self._simulate_btn.setMinimumHeight(35)
        self._simulate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color:  #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #888888;
            }
        """)
        self._simulate_btn.clicked.connect(self._on_simulate)
        layout.addWidget(self._simulate_btn)

        # --- Progress Bar ---
        self._progress_bar = QProgressBar()
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setMaximum(0)  # Indeterminate
        self._progress_bar.hide()
        layout.addWidget(self._progress_bar)

        # --- Status Label ---
        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("color: #888888; font-style: italic;")
        layout.addWidget(self._status_label)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # --- Netlist Preview Button ---
        self._netlist_btn = QPushButton("View Netlist...")
        self._netlist_btn.clicked.connect(self._on_view_netlist)
        layout.addWidget(self._netlist_btn)

        layout.addStretch()

    def _create_transient_group(self) -> QGroupBox:
        """Creates the transient analysis parameter group."""
        group = QGroupBox("Transient Parameters")
        form = QFormLayout(group)

        self._tran_step = QLineEdit("1u")
        self._tran_step.setToolTip("Time step (e.g., 1u, 10n, 100p)")
        form.addRow("Step Time:", self._tran_step)

        self._tran_stop = QLineEdit("10m")
        self._tran_stop.setToolTip("Stop time (e. g., 1m, 100u, 10s)")
        form.addRow("Stop Time:", self._tran_stop)

        return group

    def _create_ac_group(self) -> QGroupBox:
        """Creates the AC analysis parameter group."""
        group = QGroupBox("AC Parameters")
        form = QFormLayout(group)

        self._ac_start = QLineEdit("1")
        self._ac_start.setValidator(QDoubleValidator(0.001, 1e12, 3))
        form.addRow("Start Freq (Hz):", self._ac_start)

        self._ac_stop = QLineEdit("1e6")
        self._ac_stop.setValidator(QDoubleValidator(0.001, 1e12, 3))
        form.addRow("Stop Freq (Hz):", self._ac_stop)

        self._ac_points = QLineEdit("100")
        form.addRow("Points/Decade:", self._ac_points)

        return group

    def _create_dc_group(self) -> QGroupBox:
        """Creates the DC sweep parameter group."""
        group = QGroupBox("DC Sweep Parameters")
        form = QFormLayout(group)

        self._dc_source = QLineEdit("V1")
        self._dc_source.setToolTip("Source to sweep (e.g., V1)")
        form.addRow("Source:", self._dc_source)

        self._dc_start = QLineEdit("0")
        self._dc_start.setValidator(QDoubleValidator(-1e6, 1e6, 3))
        form.addRow("Start (V):", self._dc_start)

        self._dc_stop = QLineEdit("5")
        self._dc_stop.setValidator(QDoubleValidator(-1e6, 1e6, 3))
        form.addRow("Stop (V):", self._dc_stop)

        self._dc_step = QLineEdit("0.1")
        self._dc_step.setValidator(QDoubleValidator(0.0001, 1e6, 4))
        form.addRow("Step (V):", self._dc_step)

        return group

    def _on_analysis_changed(self, index: int):
        """Handles analysis type selection change."""
        analysis_type = self._analysis_combo.currentData()

        # Hide all parameter groups
        self._transient_group.hide()
        self._ac_group.hide()
        self._dc_group.hide()

        # Show relevant group
        if analysis_type == AnalysisType.TRANSIENT:
            self._transient_group.show()
        elif analysis_type == AnalysisType.AC_ANALYSIS:
            self._ac_group.show()
        elif analysis_type == AnalysisType.DC_SWEEP:
            self._dc_group.show()

    def _parse_time_value(self, text: str) -> float:
        """Parses a time value string with suffix (e.g., '1m', '100u')."""
        text = text.strip().lower()

        suffixes = {
            'f': 1e-15,
            'p': 1e-12,
            'n': 1e-9,
            'u': 1e-6,
            'm': 1e-3,
            's': 1,
            '': 1
        }

        for suffix, multiplier in suffixes.items():
            if text.endswith(suffix) and suffix:
                try:
                    return float(text[:-1]) * multiplier
                except ValueError:
                    pass

        try:
            return float(text)
        except ValueError:
            raise ValueError(f"Invalid time value: {text}")

    def _build_analysis_config(self) -> AnalysisConfig:
        """Builds the analysis configuration from UI inputs."""
        analysis_type = self._analysis_combo.currentData()

        if analysis_type == AnalysisType.OPERATING_POINT:
            return SpiceRunner.create_op_config()

        elif analysis_type == AnalysisType.TRANSIENT:
            step = self._parse_time_value(self._tran_step.text())
            stop = self._parse_time_value(self._tran_stop.text())
            return SpiceRunner.create_transient_config(
                step_time=step,
                stop_time=stop
            )

        elif analysis_type == AnalysisType.AC_ANALYSIS:
            return SpiceRunner.create_ac_config(
                start_freq=float(self._ac_start.text()),
                stop_freq=float(self._ac_stop.text()),
                num_points=int(self._ac_points.text())
            )

        elif analysis_type == AnalysisType.DC_SWEEP:
            return SpiceRunner.create_dc_sweep_config(
                source_name=self._dc_source.text().strip(),
                start_value=float(self._dc_start.text()),
                stop_value=float(self._dc_stop.text()),
                increment=float(self._dc_step.text())
            )

        raise ValueError(f"Unknown analysis type: {analysis_type}")

    def _on_simulate(self):
        """Handles simulate button click."""
        try:
            # Generate netlist
            self._status_label.setText("Generating netlist...")
            self._status_label.setStyleSheet("color: #4ECDC4;")

            generator = NetlistGenerator()
            netlist = generator.generate(self.schematic_view)
            self._last_netlist = netlist

            # Build analysis config
            config = self._build_analysis_config()

            # Check ngspice availability
            runner = SpiceRunner()
            if not runner.check_ngspice_available():
                raise NgspiceNotFoundError(
                    "ngspice is not installed.\n\n"
                    "Please install ngspice and PySpice:\n"
                    "  pip install PySpice\n\n"
                    "Then install ngspice:\n"
                    "  Windows: Download from ngspice.sourceforge.io\n"
                    "  macOS: brew install ngspice\n"
                    "  Linux: sudo apt install ngspice"
                )

            # Start simulation in background
            self._simulate_btn.setEnabled(False)
            self._progress_bar.show()
            self._status_label.setText("Running simulation...")

            self._worker = SimulationWorker(netlist, config)
            self._worker.finished.connect(self._on_simulation_finished)
            self._worker.progress.connect(self._on_simulation_progress)
            self._worker.start()

        except MissingGroundError:
            self._show_error(
                "Missing Ground",
                "Your circuit must have a ground (GND) component.\n\n"
                "Add a Ground from the component palette and connect it to your circuit."
            )
            self._status_label.setText("Error: Missing ground")
            self._status_label.setStyleSheet("color: #FF6B6B;")

        except NetlistError as e:
            self._show_error("Netlist Error", str(e))
            self._status_label.setText("Error: Netlist generation failed")
            self._status_label.setStyleSheet("color: #FF6B6B;")

        except ValueError as e:
            self._show_error("Invalid Parameters", str(e))
            self._status_label.setText("Error: Invalid parameters")
            self._status_label.setStyleSheet("color: #FF6B6B;")

        except NgspiceNotFoundError as e:
            self._show_error("ngspice Not Found", str(e))
            self._status_label.setText("Error: ngspice not found")
            self._status_label.setStyleSheet("color: #FF6B6B;")

    def _on_simulation_progress(self, message: str):
        """Handles simulation progress updates."""
        self._status_label.setText(message)

    def _on_simulation_finished(self, result):
        """Handles simulation completion."""
        self._simulate_btn.setEnabled(True)
        self._progress_bar.hide()

        if isinstance(result, Exception):
            self._show_error("Simulation Error", str(result))
            self._status_label.setText("Simulation failed")
            self._status_label.setStyleSheet("color: #FF6B6B;")
            return

        if not result.success:
            self._show_error(
                "Simulation Failed",
                f"The simulation did not complete successfully.\n\n{result.error_message}"
            )
            self._status_label.setText("Simulation failed")
            self._status_label.setStyleSheet("color: #FF6B6B;")
            return

        # Convert to SimulationData and emit
        sim_data = SimulationData.from_simulation_result(result, "Simulation Results")
        self.simulation_completed.emit(sim_data)

        self._status_label.setText("Simulation complete")
        self._status_label.setStyleSheet("color:  #4CAF50;")

    def _on_view_netlist(self):
        """Shows the generated netlist in a dialog."""
        try:
            generator = NetlistGenerator()
            netlist = generator.generate(self.schematic_view)
            self._last_netlist = netlist

            from PySide6.QtWidgets import QDialog, QTextEdit, QDialogButtonBox

            dialog = QDialog(self)
            dialog.setWindowTitle("SPICE Netlist")
            dialog.resize(500, 400)

            layout = QVBoxLayout(dialog)

            text_edit = QTextEdit()
            text_edit.setPlainText(netlist)
            text_edit.setReadOnly(True)
            text_edit.setStyleSheet("""
                QTextEdit {
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 12px;
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                }
            """)
            layout.addWidget(text_edit)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok)
            buttons.accepted.connect(dialog.accept)
            layout.addWidget(buttons)

            dialog.exec()

        except NetlistError as e:
            self._show_error("Netlist Error", str(e))

    def _show_error(self, title: str, message: str):
        """Shows an error message dialog."""
        QMessageBox.critical(self, title, message)

    def get_last_netlist(self) -> str:
        """Returns the last generated netlist."""
        return self._last_netlist
