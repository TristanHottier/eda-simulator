from PySide6.QtWidgets import QWidget, QFormLayout, QLabel, QLineEdit, QVBoxLayout
from PySide6.QtCore import Qt


class ParameterInspector(QWidget):
    def __init__(self, schematic_view):
        super().__init__()
        self.schematic_view = schematic_view
        self.current_component = None

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.form = QFormLayout()
        self.layout.addLayout(self.form)

        self.param_fields = {}

    def inspect_component(self, component_item):
        """Populate form with component parameters"""
        self.current_component = component_item

        # Clear previous form
        while self.form.rowCount():
            self.form.removeRow(0)
        self.param_fields.clear()

        # Show component reference
        self.form.addRow(QLabel("Ref"), QLabel(component_item.ref))

        # Get model
        comp_model = self.get_model_from_item(component_item)

        # If model has no parameters yet, add defaults
        if not comp_model.parameters:
            comp_model.parameters = self.default_parameters(comp_model)

        # Add editable fields
        for key, value in comp_model.parameters.items():
            line_edit = QLineEdit(str(value))
            line_edit.editingFinished.connect(lambda k=key, le=line_edit: self.update_parameter(k, le))
            self.form.addRow(QLabel(key), line_edit)
            self.param_fields[key] = line_edit

    def update_parameter(self, key, line_edit):
        """Update the model as soon as user edits a field"""
        if not self.current_component:
            return

        comp_model = self.get_model_from_item(self.current_component)
        val = line_edit.text()
        try:
            if '.' in val:
                val = float(val)
            else:
                val = int(val)
        except ValueError:
            pass  # leave as string if not number

        comp_model.parameters[key] = val

        # Optional: update label on schematic
        if key.lower() in ["ref", "name"]:
            self.current_component.label.setPlainText(str(val))

    def get_model_from_item(self, item):
        """Find the Component model corresponding to a ComponentItem"""
        for comp in self.schematic_view.components:
            if comp.ref == item.ref:
                return comp
        return None

    def default_parameters(self, comp_model):
        """Return default parameters based on type"""
        comp_type = comp_model.parameters.get("type", "generic").lower()
        if comp_type == "resistor":
            return {"resistance": 1000, "type": "resistor"}
        elif comp_type == "capacitor":
            return {"capacitance": 1e-6, "type": "capacitor"}
        elif comp_type == "led":
            return {"voltage_drop": 2.0, "type": "led"}
        else:
            return {"type": comp_type}
