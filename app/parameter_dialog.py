# app/parameter_dialog.py
from typing import Dict, Any, Optional, Union
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QLabel,
    QDialogButtonBox, QVBoxLayout
)
from PySide6.QtGui import QDoubleValidator
from ui.undo_commands import ParameterChangeCommand


class ParameterDialog(QDialog):
    """
    Popup dialog to edit all parameters of a Component model.
    Automatically creates fields for all keys in Component.parameters.
    """
    UNIT_MAP = {"resistance": "Ω", "capacitance": "µF", "voltage_drop": "V"}

    def __init__(self, component_item, component_model, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit {component_item.ref}")
        self.component_item = component_item
        self.component_model = component_model

        # Maps parameter keys to their respective QLineEdit widgets
        self.fields: Dict[str, QLineEdit] = {}

        self.setup_ui()

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Generate rows for every parameter in the model
        for key, val in self.component_model.all_parameters():
            unit = self.UNIT_MAP.get(key.lower(), "")
            label_text = f"{key} ({unit})" if unit else key

            line_edit = QLineEdit(str(val))

            # If the value is numeric, restrict input to numbers
            if isinstance(val, (int, float)):
                line_edit.setValidator(QDoubleValidator())

            form_layout.addRow(QLabel(label_text), line_edit)
            self.fields[key] = line_edit

        main_layout.addLayout(form_layout)

        # Standard OK/Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def _convert_value(self, text: str) -> Union[int, float, str]:
        """Attempts to cast string input back to numeric types."""
        try:
            if "." in text:
                return float(text)
            return int(text)
        except ValueError:
            return text

    def accept(self) -> None:
        """Process changes and push to undo stack before closing."""
        view = self.component_item.scene().views()[0] if self.component_item.scene() else None
        undo_stack = getattr(view, "undo_stack", None)

        for key, line_edit in self.fields.items():
            new_val = self._convert_value(line_edit.text())
            old_val = self.component_model.parameters.get(key)

            if new_val != old_val:
                if undo_stack:
                    undo_stack.push(ParameterChangeCommand(
                        self.component_model, key, old_val, new_val,
                        component_item=self.component_item
                    ))
                else:
                    # Fallback if no undo stack is available
                    self.component_model.parameters[key] = new_val
                    self.component_item.refresh_label()

        super().accept()