from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QFileDialog

class SettingsDialog(QDialog):
    def __init__(self, blender_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Blender executable:"))
        self.blender = QLineEdit(blender_path)
        lay.addWidget(self.blender)
        br = QHBoxLayout()
        b = QPushButton("Browse"); b.clicked.connect(self.browse)
        br.addWidget(b); br.addStretch()
        lay.addLayout(br)
        ok = QPushButton("OK"); ok.clicked.connect(self.accept); lay.addWidget(ok)
    def browse(self):
        p,_ = QFileDialog.getOpenFileName(self, "Select blender.exe", "", "Executable (*.exe)")
        if p: self.blender.setText(p)
