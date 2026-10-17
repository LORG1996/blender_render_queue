import sys, os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Blender Batch Queue Manager")
    app.setOrganizationName("BatchRenderer")

    blender_exe = r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe"
    if os.path.exists(blender_exe):
        app.setWindowIcon(QIcon(blender_exe))

    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
