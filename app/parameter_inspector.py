# app/parameter_inspector.py
from typing import Dict, Any, Union, Optional, TYPE_CHECKING
from PySide6.QtWidgets import QWidget, QFormLayout, QLabel, QLineEdit, QVBoxLayout
from PySide6.QtCore import Qt
from ui.undo_commands import ParameterChangeCommand

if TYPE_CHECKING:
    from ui.schematic_view import SchematicView
    from ui.component_item import ComponentItem


class ParameterInspector(QWidget):
    """
    A side-panel widget that displays and allows editing of 
    the selected component's parameters in real-time.
    """

    def __init__(self, schematic_view: 'SchematicView'):
        super().__init__()
        self.schematic_view = schematic_view
        self.current_item: Optional['ComponentItem'] = None

        self.main_layout = QVBoxLayout(self)
        self.form = QFormLayout()
        self.main_layout.addLayout(self.form)

        # Track active line edits to prevent garbage collection issues
        self.param_fields: Dict[str, QLineEdit] = {}

    def inspect_component(self, component_item: 'ComponentItem') -> None:
        """Populates the form with parameters from the selected component."""
        self.current_item = component_item
        model = component_item.model

        # Clear existing rows
        while self.form.rowCount():
            self.form.removeRow(0)
        self.param_fields.clear()

        # Header Info
        self.form.addRow(QLabel("<b>Reference:</b>"), QLabel(component_item.ref))
        self.form.addRow(QLabel("<b>Type:</b>"), QLabel(model.type.capitalize()))

        # Generate editable fields for all parameters
        for key, value in model.parameters.items():
            line_edit = QLineEdit(str(value))
            # Use a lambda with default arguments to capture 'key' and 'line_edit' correctly
            line_edit.editingFinished.connect(
                lambda k=key, le=line_edit: self._on_parameter_edited(k, le)
            )

            self.form.addRow(QLabel(key), line_edit)
            self.param_fields[key] = line_edit

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
        while self.form.rowCount():
            self.form.removeRow(0)
        self.param_fields.clear()
        self.form.addRow(QLabel("<i>No component selected</i>"))