# app/parameter_inspector.py
from typing import Dict, Any, Union, Optional, TYPE_CHECKING
from PySide6.QtWidgets import QWidget, QFormLayout, QLabel, QLineEdit, QVBoxLayout, QComboBox, QScrollArea
from PySide6.QtCore import Qt, QTimer
from functools import partial
from ui.undo_commands import ParameterChangeCommand

if TYPE_CHECKING:
    from ui.schematic_view import SchematicView
    from ui.component_item import ComponentItem


class ParameterInspector(QWidget):
    """
    A side-panel widget that displays and allows editing of 
    the selected component's parameters in real-time.
    """
    DIODE_TYPE_PARAM_MAP = {
        "silicon": ["IS", "N", "TT"],
        "schottky": ["IS", "N", "TT"],
        "zener": ["IS", "N", "BV", "IBV"],
    }

    DIODE_TYPE_LABELS = {
        "silicon": "Silicon",
        "schottky": "Schottky",
        "zener": "Zener"
    }

    TRANSISTOR_TYPE_PARAM_MAP = {
        "npn": ["IS", "BF", "NF", "VAF", "IKF", "CJE", "CJC", "TF"],
        "pnp": ["IS", "BF", "NF", "VAF", "IKF", "CJE", "CJC", "TF"],
        "nmos": ["KP", "LAMBDA", "CGS", "CGD", "CBD", "VTO"],
        "pmos": ["KP", "LAMBDA", "CGS", "CGD", "CBD", "VTO"]
    }

    # Dropdown labels for UI
    TRANSISTOR_TYPE_LABELS = {
        "npn": "NPN BJT",
        "pnp": "PNP BJT",
        "nmos": "N-MOSFET",
        "pmos": "P-MOSFET"
    }

    def __init__(self, schematic_view: 'SchematicView'):
        super().__init__()
        self.schematic_view = schematic_view
        self.current_item: Optional['ComponentItem'] = None

        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Important to allow resizing
        scroll_content = QWidget()  # The content inside the scroll area
        scroll_area.setWidget(scroll_content)

        # Layout inside scroll area
        self.form = QFormLayout(scroll_content)

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(scroll_area)

        # Track active line edits to prevent garbage collection issues
        self.param_fields: Dict[str, QLineEdit] = {}

        # Keep reference to avoid GC
        self.diode_type_combo: Optional[QComboBox] = None
        self.transistor_type_combo: Optional[QComboBox] = None

    def inspect_component(self, component_item: 'ComponentItem') -> None:
        """Populates the form with parameters from the selected component."""
        self.current_item = component_item
        model = component_item.model

        # --- Remove All Form Rows and Widgets Safely ---
        for i in reversed(range(self.form.rowCount())):
            label_item = self.form.itemAt(i, QFormLayout.LabelRole)
            if label_item is not None:
                widget = label_item.widget()
                if widget is not None:
                    widget.deleteLater()
            field_item = self.form.itemAt(i, QFormLayout.FieldRole)
            if field_item is not None:
                widget = field_item.widget()
                if widget is not None:
                    widget.deleteLater()
            self.form.removeRow(i)

        self.param_fields.clear()
        self.diode_type_combo = None
        self.transistor_type_combo = None

        # Header Info
        self.form.addRow(QLabel("<b>Reference:</b>"), QLabel(component_item.ref))
        self.form.addRow(QLabel("<b>Type:</b>"), QLabel(model.type.capitalize()))

        # Generate editable fields for all parameters
        if model.type == "diode":
            # Diode type dropdown (silicon/schottky/zener)
            diode_type = model.parameters.get("diode_type", "silicon")
            self.diode_type_combo = QComboBox()
            for k in ["silicon", "schottky", "zener"]:
                self.diode_type_combo.addItem(self.DIODE_TYPE_LABELS[k], k)
            self.diode_type_combo.setCurrentIndex(
                ["silicon", "schottky", "zener"].index(diode_type)
            )
            self.diode_type_combo.currentIndexChanged.connect(self._on_diode_type_changed)
            self.form.addRow(QLabel("diode_type"), self.diode_type_combo)

            # Show only relevant parameter fields (not 'type' or 'diode_type')
            for key in self.DIODE_TYPE_PARAM_MAP[diode_type]:
                val = model.parameters.get(key, "")
                line_edit = QLineEdit(str(val))
                line_edit.editingFinished.connect(partial(self._on_parameter_edited, key, line_edit))
                self.form.addRow(QLabel(key), line_edit)
                self.param_fields[key] = line_edit

        elif model.type == "transistor":
            # Transistor type dropdown (npn/pnp/nmos/pmos)
            transistor_type = model.parameters.get("type", "npn")
            self.transistor_type_combo = QComboBox()
            for k in ["npn", "pnp", "nmos", "pmos"]:
                self.transistor_type_combo.addItem(k.upper(), k)

            self.transistor_type_combo.setCurrentIndex(
                ["npn", "pnp", "nmos", "pmos"].index(transistor_type)
            )

            self.transistor_type_combo.currentIndexChanged.connect(self._on_transistor_type_changed)
            self.form.addRow(QLabel("transistor_type"), self.transistor_type_combo)

            # Show only relevant parameter fields for the selected transistor type
            for key in self.TRANSISTOR_TYPE_PARAM_MAP[transistor_type]:
                val = model.parameters.get(key, "")
                line_edit = QLineEdit(str(val))
                line_edit.editingFinished.connect(partial(self._on_parameter_edited, key, line_edit))
                self.form.addRow(QLabel(key), line_edit)
                self.param_fields[key] = line_edit

        else:
            # Non-diode regular parameter editing (as before)
            for key, value in model.parameters.items():
                line_edit = QLineEdit(str(value))
                line_edit.editingFinished.connect(partial(self._on_parameter_edited, key, line_edit))
                self.form.addRow(QLabel(key), line_edit)
                self.param_fields[key] = line_edit

    def _on_diode_type_changed(self, idx: int) -> None:
        """Handle the diode type dropdown changing."""
        if not self.current_item:
            return
        model = self.current_item.model
        new_type = self.diode_type_combo.currentData()
        old_type = model.parameters.get("diode_type", "silicon")

        if new_type != old_type:
            undo_stack = self.schematic_view.undo_stack
            if undo_stack:
                undo_stack.push(ParameterChangeCommand(
                    model, "diode_type", old_type, new_type,
                    component_item=self.current_item
                ))
            else:
                model.parameters["diode_type"] = new_type
                self.current_item.refresh_label()

            # The parameters visible/necessary change, so refresh UI
            self.current_item.update_symbol()
            QTimer.singleShot(0, partial(self.inspect_component, self.current_item))

    def _on_transistor_type_changed(self, idx: int) -> None:
        """Handle the transistor type dropdown changing, diode-style (no DEFAULT_PARAMS needed)."""
        if not self.current_item:
            return

        model = self.current_item.model
        new_type = self.transistor_type_combo.currentData()
        old_type = model.parameters.get("type", "npn")

        if new_type != old_type:
            # Update the type in the model (undoable if undo stack exists)
            undo_stack = self.schematic_view.undo_stack
            if undo_stack:
                undo_stack.push(ParameterChangeCommand(
                    model, "type", old_type, new_type,
                    component_item=self.current_item
                ))
            else:
                model.parameters["type"] = new_type
                self.current_item.refresh_label()

            # Refresh the component symbol in the schematic
            self.current_item.update_symbol()

            # Refresh the inspector UI to show only the parameters relevant to the new type
            # (TRANSISTOR_TYPE_PARAM_MAP defines which fields are shown)
            QTimer.singleShot(0, partial(self.inspect_component, self.current_item))

    def _convert_value(self, text: str) -> Union[int, float, str]:
        """Casts string input to appropriate numeric types if possible."""
        try:
            if "." in text:
                return float(text)
            return int(text)
        except ValueError:
            return text

    def _on_parameter_edited(self, key: str, line_edit: QLineEdit) -> None:
        """Handles the logic for updating the model when a field is edited."""
        if not self.current_item:
            return

        model = self.current_item.model
        new_val = self._convert_value(line_edit.text())
        old_val = model.parameters.get(key)

        if new_val != old_val:
            undo_stack = self.schematic_view.undo_stack
            if undo_stack:
                undo_stack.push(ParameterChangeCommand(
                    model, key, old_val, new_val,
                    component_item=self.current_item
                ))
            else:
                model.parameters[key] = new_val
                self.current_item.refresh_label()

    def clear_inspector(self) -> None:
        """Clears the inspector when no component is selected."""
        self.current_item = None
        for i in reversed(range(self.form.rowCount())):
            label_item = self.form.itemAt(i, QFormLayout.LabelRole)
            if label_item is not None and label_item.widget() is not None:
                label_item.widget().deleteLater()
            field_item = self.form.itemAt(i, QFormLayout.FieldRole)
            if field_item is not None and field_item.widget() is not None:
                field_item.widget().deleteLater()
            self.form.removeRow(i)
        self.param_fields.clear()
        self.diode_type_combo = None
        self.form.addRow(QLabel("<i>No component selected</i>"))