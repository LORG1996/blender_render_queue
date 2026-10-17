from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar

class TaskWidget(QWidget):
    def __init__(self, task):
        super().__init__()
        lay = QHBoxLayout(self)
        thumb = QLabel(); thumb.setFixedSize(64,64)
        lay.addWidget(thumb)
        info = QVBoxLayout()
        info.addWidget(QLabel(task.get("path","")))
        info.addWidget(QLabel(task.get("scene","")))
        info.addWidget(QLabel(task.get("camera","")))
        info.addWidget(QLabel(task.get("compositor","")))
        pb = QProgressBar()
        info.addWidget(pb)
        lay.addLayout(info)
