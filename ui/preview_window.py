from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage
from PIL import Image
import os, glob

class PreviewWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Render Preview")
        self.resize(900, 650)
        lay = QVBoxLayout(self)
        self.label = QLabel("No preview yet")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("background:#1e1e1e; color:#e0e0e0;")
        lay.addWidget(self.label)
        self.timer = QTimer()
        self.timer.timeout.connect(self.poll)
        self.folder = ""

    def set_folder(self, folder):
        self.folder = folder
        try:
            os.makedirs(folder, exist_ok=True)
        except OSError:
            pass
        if not self.timer.isActive():
            self.timer.start(1000)
        self.show()
        self.raise_()
        self.activateWindow()

    def poll(self):
        if not self.folder or not os.path.isdir(self.folder):
            return
        imgs = [f for f in glob.glob(os.path.join(self.folder, "*")) if f.lower().endswith((".png", ".jpg", ".jpeg", ".exr", ".bmp"))]
        if imgs:
            latest = max(imgs, key=os.path.getmtime)
            self.show_image(latest)

    def show_image(self, path):
        try:
            im = Image.open(path).convert("RGBA")
            data = im.tobytes("raw", "RGBA")
            qimg = QImage(data, im.width, im.height, QImage.Format_RGBA8888)
            pix = QPixmap.fromImage(qimg).scaled(self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.label.setPixmap(pix)
        except Exception:
            pass
