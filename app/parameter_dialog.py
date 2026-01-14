from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QLabel, QDialogButtonBox, QVBoxLayout
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
        self.fields = {}  # key -> QLineEdit

        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()
        layout.addLayout(form)

        # --- Create a field for every parameter ---
        for key, val in self.component_model.all_parameters():
            label_text = key
            unit = self.UNIT_MAP.get(key.lower(), "")
            if unit:
                label_text += f" ({unit})"

            line_edit = QLineEdit(str(val))
            # accept only numbers if value is int/float
            if isinstance(val, (int, float)):
                line_edit.setValidator(QDoubleValidator())
            form.addRow(QLabel(label_text), line_edit)
            self.fields[key] = line_edit

        # --- Ok / Cancel buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        # Update the component model with values from fields
        for key, line_edit in self.fields.items():
            text = line_edit.text()
            try:
                if "." in text:
                    val = float(text)
                else:
                    val = int(text)
            except ValueError:
                val = text

            old_val = self.component_model.parameters.get(key, None)
            if old_val != val:
                # get the view's undo stack
                view = self.component_item.scene().views()[0] if self.component_item.scene().views() else None
                if view and hasattr(view, "undo_stack"):
                    view.undo_stack.push(ParameterChangeCommand(self.component_item, key, old_val, val))
                else:
                    # fallback: update directly if no undo_stack yet
                    self.component_model.parameters[key] = val

        # Update component label with main key if exists
        main_key = next(
            (k for k in ["resistance", "capacitance", "voltage_drop"]
             if k in self.component_model.parameters),
            None
        )
        if main_key:
            val = self.component_model.get_parameter(main_key)
            unit = self.UNIT_MAP.get(main_key, "")
            self.component_item.label.setPlainText(f"{self.component_item.ref} {val}{unit}")
        else:
            self.component_item.label.setPlainText(self.component_item.ref)

        super().accept()
