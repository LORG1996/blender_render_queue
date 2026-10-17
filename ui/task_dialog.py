from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QSpinBox, QPushButton, QLabel, QFileDialog, QProgressDialog, QCheckBox
from PySide6.QtCore import QThread, Signal, Qt
from utils.blend_parser import list_scenes, list_cameras, list_compositors


class BlendLoader(QThread):
    progress = Signal(str)
    finished = Signal(dict)

    def __init__(self, blender_exe, blend_path, scene_name=None):
        super().__init__()
        self.blender_exe = blender_exe
        self.blend_path = blend_path
        self.scene_name = scene_name

    def run(self):
        result = {}
        self.progress.emit("Reading scenes...")
        result["scenes"] = list_scenes(self.blender_exe, self.blend_path) if self.blender_exe else []
        scene = self.scene_name or (result["scenes"][0] if result["scenes"] else None)
        self.progress.emit("Reading cameras...")
        result["cameras"] = list_cameras(self.blender_exe, self.blend_path, scene) if self.blender_exe else []
        self.progress.emit("Reading compositors...")
        result["compositors"] = list_compositors(self.blender_exe, self.blend_path) if self.blender_exe else []
        result["scene"] = scene
        self.finished.emit(result)


class TaskSettingsDialog(QDialog):
    def __init__(self, task, blender_exe, parent=None):
        super().__init__(parent)
        self.task = task
        self.blender = blender_exe
        self.setWindowTitle("Task settings")
        self.resize(520, 420)

        lay = QVBoxLayout(self)

        lay.addWidget(QLabel("Scene"))
        self.scene = QComboBox()
        lay.addWidget(self.scene)

        lay.addWidget(QLabel("Camera"))
        self.camera = QComboBox()
        lay.addWidget(self.camera)

        lay.addWidget(QLabel("Compositor"))
        self.comp = QComboBox()
        lay.addWidget(self.comp)

        fr = QHBoxLayout()
        self.start = QSpinBox(); self.end = QSpinBox(); self.step = QSpinBox()
        for sp in (self.start, self.end, self.step):
            sp.setRange(1, 1000000)
            sp.setValue(1)
        fr.addWidget(QLabel("Start")); fr.addWidget(self.start)
        fr.addWidget(QLabel("End")); fr.addWidget(self.end)
        fr.addWidget(QLabel("Step")); fr.addWidget(self.step)
        lay.addLayout(fr)

        out = QHBoxLayout()
        self.outdir = QLineEdit(task.get("outdir", ""))
        b = QPushButton("Browse"); b.clicked.connect(self.browse)
        out.addWidget(self.outdir); out.addWidget(b)
        lay.addLayout(out)

        self.std_out = QCheckBox("Standard Output (e.g. MP4 from scene)")
        self.std_out.setChecked(task.get("standard_output", True))
        lay.addWidget(self.std_out)

        self.status = QLabel("Loading scene data...")
        self.status.setStyleSheet("color:#888; font-style:italic;")
        lay.addWidget(self.status)

        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        lay.addWidget(ok)

        self.start.setValue(int(self.task.get("start", 1)))
        self.end.setValue(int(self.task.get("end", 1)))
        self.step.setValue(int(self.task.get("step", 1)))

        self.prog = QProgressDialog("Loading blend data...", "Cancel", 0, 100, self)
        self.prog.setWindowTitle("Task settings")
        self.prog.setWindowModality(Qt.ApplicationModal)
        self.prog.setCancelButton(None)
        self.prog.show()

        self.loader = BlendLoader(self.blender, self.task["path"], self.task.get("scene") or "")
        self.loader.progress.connect(self.prog.setLabelText)
        self.loader.finished.connect(self.on_loaded)
        self.loader.start()

    def browse(self):
        d = QFileDialog.getExistingDirectory(self, "Output dir")
        if d:
            self.outdir.setText(d)

    def on_loaded(self, result):
        self.prog.hide()
        self.status.hide()
        scenes = result.get("scenes", [])
        cameras = result.get("cameras", [])
        comps = result.get("compositors", [])
        self.scene.addItems(scenes)
        self.camera.addItems(cameras)
        self.comp.addItems(comps)
        if self.task.get("scene") in scenes:
            self.scene.setCurrentText(self.task["scene"])
        elif scenes:
            self.scene.setCurrentText(scenes[0])
        if self.task.get("camera") in cameras:
            self.camera.setCurrentText(self.task["camera"])
        if self.task.get("compositor") in comps:
            self.comp.setCurrentText(self.task["compositor"])

        self.scene.currentTextChanged.connect(self.refresh_cameras)
        self.scene.currentTextChanged.connect(self.refresh_compositors)

    def refresh_cameras(self):
        scene = self.scene.currentText()
        if not scene or not self.blender:
            return
        cams = list_cameras(self.blender, self.task["path"], scene)
        self.camera.blockSignals(True)
        self.camera.clear()
        self.camera.addItems(cams)
        if self.task.get("camera") in cams:
            self.camera.setCurrentText(self.task["camera"])
        self.camera.blockSignals(False)

    def refresh_compositors(self):
        if not self.blender:
            return
        comps = list_compositors(self.blender, self.task["path"])
        self.comp.blockSignals(True)
        self.comp.clear()
        self.comp.addItems(comps)
        if self.task.get("compositor") in comps:
            self.comp.setCurrentText(self.task["compositor"])
        self.comp.blockSignals(False)

    def accept(self):
        self.task["scene"] = self.scene.currentText()
        self.task["camera"] = self.camera.currentText()
        self.task["compositor"] = self.comp.currentText()
        self.task["start"] = self.start.value()
        self.task["end"] = self.end.value()
        self.task["step"] = self.step.value()
        self.task["outdir"] = self.outdir.text()
        self.task["standard_output"] = self.std_out.isChecked()
        super().accept()
