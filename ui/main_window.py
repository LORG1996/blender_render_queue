from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QTextEdit, QFileDialog, QMessageBox, QAbstractItemView,
    QSplitter, QLabel, QProgressBar, QStatusBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPalette, QColor
from core.queue_manager import QueueManager
from ui.settings_dialog import SettingsDialog
from ui.task_dialog import TaskSettingsDialog
from core.blender_process import BlenderProcess
import os, tempfile, json, re
from PIL import Image
from PySide6.QtGui import QPixmap, QImage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blender Batch Queue Manager — PySide6")
        self.resize(1300, 800)
        self.qm = QueueManager()
        self.blender_exe = r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe"
        self.last_saved_path = ""
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.poll_preview)
        self.spinner_timer = QTimer()
        self.spinner_timer.timeout.connect(self.tick_spinner)
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_idx = 0

        root = QWidget()
        self.setCentralWidget(root)
        lay = QVBoxLayout(root)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        top = QHBoxLayout()
        self.add_btn = QPushButton("Add .blend")
        self.copy_btn = QPushButton("Copy")
        self.up_btn = QPushButton("Up")
        self.down_btn = QPushButton("Down")
        self.delete_btn = QPushButton("Delete")
        self.save_btn = QPushButton("Save Preset")
        self.load_btn = QPushButton("Load Preset")
        self.start_btn = QPushButton("Start Queue")
        self.stop_btn = QPushButton("Stop")
        self.settings_btn = QPushButton("Settings")
        for b in (self.add_btn, self.copy_btn, self.up_btn, self.down_btn,
                  self.delete_btn, self.save_btn, self.load_btn,
                  self.start_btn, self.stop_btn, self.settings_btn):
            top.addWidget(b)
        top.addStretch()
        lay.addLayout(top)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "Enabled", "Std Output", "File", "Scene", "Camera",
            "Compositor", "Frames", "Output", "Status"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_task)
        self.table.itemChanged.connect(self.on_item_changed)
        lay.addWidget(self.table, stretch=2)

        splitter = QSplitter(Qt.Horizontal)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Blender render logs appear here...")
        splitter.addWidget(self.log)

        self.preview_label = QLabel("No preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet(
            "background:#141414; color:#888; border:1px solid #333;"
        )
        splitter.addWidget(self.preview_label)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        lay.addWidget(splitter, stretch=1)

        bottom = QHBoxLayout()
        self.spinner_label = QLabel("")
        self.spinner_label.setStyleSheet("color:#007acc; font-family:monospace; font-weight:bold;")
        bottom.addWidget(self.spinner_label)
        bottom.addStretch()
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        lay.addLayout(bottom)

        self.add_btn.clicked.connect(self.add_blend)
        self.copy_btn.clicked.connect(self.copy_task)
        self.up_btn.clicked.connect(self.move_up)
        self.down_btn.clicked.connect(self.move_down)
        self.delete_btn.clicked.connect(self.delete_task)
        self.start_btn.clicked.connect(self.start_queue)
        self.stop_btn.clicked.connect(self.stop_all)
        self.settings_btn.clicked.connect(self.open_settings)
        self.save_btn.clicked.connect(self.save_preset)
        self.load_btn.clicked.connect(self.load_preset)

        self.set_dark_blender_style()

    def set_dark_blender_style(self):
        pal = QPalette()
        bg = QColor("#222222"); fg = QColor("#e0e0e0")
        pal.setColor(QPalette.Window, bg)
        pal.setColor(QPalette.WindowText, fg)
        pal.setColor(QPalette.Base, QColor("#1a1a1a"))
        pal.setColor(QPalette.AlternateBase, QColor("#2a2a2a"))
        pal.setColor(QPalette.Text, fg)
        pal.setColor(QPalette.Button, QColor("#333333"))
        pal.setColor(QPalette.ButtonText, fg)
        pal.setColor(QPalette.Highlight, QColor("#007acc"))
        pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        self.setPalette(pal)
        self.setStyleSheet("""
        QMainWindow { background: #222222; }
        QTableWidget { background: #1a1a1a; color: #e0e0e0; gridline-color: #333333;
                       selection-background-color: #007acc; }
        QHeaderView::section { background: #333333; color: #e0e0e0; padding: 6px;
                               border: 1px solid #444; }
        QTextEdit { background: #1a1a1a; color: #e0e0e0; border: 1px solid #333; }
        QPushButton { background: #333333; color: #e0e0e0; padding: 6px 14px;
                      border: 1px solid #444; border-radius: 4px; }
        QPushButton:hover { background: #3d3d3d; }
        QPushButton:pressed { background: #2a2a2a; }
        QStatusBar { background: #222222; color: #aaa; border-top: 1px solid #333; }
        QLabel { color: #e0e0e0; }
        """)

    def refresh_table(self):
        sel = self.table.currentRow()
        self.table.setRowCount(0)
        for t in self.qm.tasks:
            row = self.table.rowCount()
            self.table.insertRow(row)
            cb = QTableWidgetItem()
            cb.setCheckState(Qt.Checked if t.get("enabled", True) else Qt.Unchecked)
            cb.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            self.table.setItem(row, 0, cb)
            cb2 = QTableWidgetItem()
            cb2.setCheckState(Qt.Checked if t.get("standard_output", True) else Qt.Unchecked)
            cb2.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            self.table.setItem(row, 1, cb2)
            vals = [
                os.path.basename(t["path"]),
                t.get("scene", ""),
                t.get("camera", ""),
                t.get("compositor", ""),
                f"{t.get('start',1)}-{t.get('end',1)}x{t.get('step',1)}",
                t.get("outdir", ""),
                t.get("status", "Queued"),
            ]
            for c, v in enumerate(vals, start=2):
                item = QTableWidgetItem(v)
                self.table.setItem(row, c, item)
        if 0 <= sel < self.table.rowCount():
            self.table.selectRow(sel)

    def add_blend(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select blend", "", "Blender (*.blend)")
        if p:
            self.qm.add({
                "path": p, "scene": "", "camera": "", "compositor": "",
                "start": 1, "end": 1, "step": 1, "outdir": "",
                "status": "Queued", "enabled": True, "standard_output": True,
            })
            self.refresh_table()
            self.edit_task()

    def open_settings(self):
        d = SettingsDialog(self.blender_exe, self)
        if d.exec():
            self.blender_exe = d.blender.text()

    def edit_task(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.qm.tasks):
            d = TaskSettingsDialog(self.qm.tasks[row], self.blender_exe, self)
            if d.exec():
                self.refresh_table()
                self.table.selectRow(row)

    def on_item_changed(self, item):
        if item.column() == 0 and 0 <= item.row() < len(self.qm.tasks):
            self.qm.tasks[item.row()]["enabled"] = item.checkState() == Qt.Checked
        elif item.column() == 1 and 0 <= item.row() < len(self.qm.tasks):
            self.qm.tasks[item.row()]["standard_output"] = item.checkState() == Qt.Checked

    def delete_task(self):
        rows = sorted({it.row() for it in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            if 0 <= r < len(self.qm.tasks):
                del self.qm.tasks[r]
        self.refresh_table()

    def move_up(self):
        row = self.table.currentRow()
        if row > 0:
            self.qm.move_up(row)
            self.refresh_table()
            self.table.selectRow(row - 1)

    def move_down(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.qm.tasks) - 1:
            self.qm.move_down(row)
            self.refresh_table()
            self.table.selectRow(row + 1)

    def copy_task(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.qm.tasks):
            self.qm.duplicate(row)
            self.refresh_table()
            self.table.selectRow(len(self.qm.tasks) - 1)

    def save_preset(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Preset", "", "JSON (*.json)")
        if path:
            data = {"tasks": self.qm.tasks}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def load_preset(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Preset", "", "JSON (*.json)")
        if path:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.qm.tasks = data.get("tasks", [])
            self.refresh_table()

    def start_queue(self):
        if not self.blender_exe or not self.qm.tasks:
            QMessageBox.warning(self, "Missing", "Set blender path and add tasks")
            return
        self.enabled_tasks = [t for t in self.qm.tasks if t.get("enabled", True)]
        if not self.enabled_tasks:
            QMessageBox.warning(self, "Missing", "No enabled tasks in queue")
            return
        self.log.clear()
        self.preview_label.clear()
        self.last_saved_path = ""
        self.status_bar.showMessage("Rendering queue...")
        self.spinner_timer.start(100)
        self.preview_timer.start(1000)
        self.run_next(0)

    def poll_preview(self):
        if self.last_saved_path and os.path.isfile(self.last_saved_path):
            self.show_preview(self.last_saved_path)

    def show_preview(self, path):
        try:
            im = Image.open(path).convert("RGBA")
            data = im.tobytes("raw", "RGBA")
            qimg = QImage(data, im.width, im.height, QImage.Format_RGBA8888)
            pix = QPixmap.fromImage(qimg).scaled(
                self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.preview_label.setPixmap(pix)
        except Exception:
            pass

    def tick_spinner(self):
        self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner_chars)
        self.spinner_label.setText(self.spinner_chars[self.spinner_idx])

    def _on_progress(self, line):
        self.log.append(line)
        m = re.search(r"Saved:\s*['\"]([^'\"]+)['\"]", line)
        if m:
            self.last_saved_path = m.group(1)
        m2 = re.search(r"Fra:(\d+)", line)
        if m2:
            self.status_bar.showMessage(f"Frame {m2.group(1)} rendering...")

    def run_next(self, idx):
        if idx >= len(self.enabled_tasks):
            self.log.append("Queue finished")
            self.status_bar.showMessage("Queue finished")
            self.spinner_timer.stop()
            self.preview_timer.stop()
            self.spinner_label.setText("")
            return
        t = self.enabled_tasks[idx]
        t["status"] = "Rendering"
        self.refresh_table()
        self.log.append(f"Rendering {idx+1}/{len(self.enabled_tasks)}: {os.path.basename(t['path'])}")

        script = (
            "import bpy,os\n"
        )
        if t.get("scene"):
            script += f"s=bpy.data.scenes[{t['scene']!r}]\n"
        else:
            script += "s=bpy.context.scene\n"
        script += (
            f"s.frame_start={int(t.get('start',1))}\n"
            f"s.frame_end={int(t.get('end',1))}\n"
            f"s.frame_step={int(t.get('step',1))}\n"
            f"s.frame_current={int(t.get('start',1))}\n"
        )
        if t.get("camera"):
            script += f"s.camera = bpy.data.objects.get({t['camera']!r})\n"
        if t.get("outdir"):
            script += f"s.render.filepath = r'{t['outdir']}'\n"
        script += f"bpy.context.window.scene = s\n"
        script += (
            "try:\n"
            "    bpy.ops.render.render(animation=True)\n"
            "    print('RENDER_DONE')\n"
            "except Exception as e:\n"
            "    print('RENDER_ERROR:'+str(e))\n"
        )
        script += "bpy.ops.wm.quit_blender()\n"

        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(script)
            script_path = f.name

        args = [t["path"], "-b", "--python-exit-code", "1", "--python", script_path]
        self.proc = BlenderProcess(self.blender_exe, args)
        self.proc.progress.connect(self._on_progress)
        def done(ok, sp=script_path):
            try:
                os.remove(sp)
            except OSError:
                pass
            t["status"] = "Completed" if ok else "Failed"
            self.refresh_table()
            self.run_next(idx + 1)
        self.proc.finished_job.connect(done)
        self.proc.start()

    def stop_all(self):
        self.spinner_timer.stop()
        self.preview_timer.stop()
        if hasattr(self, "proc"):
            self.proc.stop()
        self.log.append("Stopped")
        self.status_bar.showMessage("Stopped")
