from PySide6.QtWidgets import QMainWindow
from ui.schematic_view import SchematicView


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python EDA Simulator")
        self.setGeometry(100, 100, 1200, 800)

        # Central widget = schematic view
        self.schematic_view = SchematicView()
        self.setCentralWidget(self.schematic_view)
