# --- THE OVERKILL PATCH START (MUST BE LINE 1) ---
import PySpice.Spice.NgSpice.Shared as NgSpiceSharedModule
import os


def dummy_check_version(self):
    pass


# Force the dummy function and the library name BEFORE anything else loads
NgSpiceSharedModule.NgSpiceShared._check_version = dummy_check_version
NgSpiceSharedModule.NgSpiceShared.LIBRARY_NAME = 'ngspice'
# --- THE OVERKILL PATCH END ---

os.environ['SPICE_SCRIPTS'] = r"C:\ngspice-45.2_dll_64\Spice64_dll\share\ngspice\scripts"
os.environ['NGSPICE_INPUT_DIR'] = r"C:\Spice64\lib\ngspice"

import sys
from PySide6.QtWidgets import QApplication
from app.app_window import AppWindow  # Now this can safely import SpiceRunner


def main():
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
