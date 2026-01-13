from PySide6.QtWidgets import QApplication
from app.app_window import AppWindow
import sys


def main():
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
