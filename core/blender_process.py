import subprocess
from PySide6.QtCore import QThread, Signal

class BlenderProcess(QThread):
    progress = Signal(str)
    finished_job = Signal(bool)

    def __init__(self, blender_exe, args):
        super().__init__()
        self.blender_exe = blender_exe
        self.args = args
        self.proc = None

    def run(self):
        cmd = [self.blender_exe, "-b"] + self.args
        try:
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in self.proc.stdout:
                self.progress.emit(line.rstrip())
            self.proc.wait()
            self.finished_job.emit(self.proc.returncode == 0)
        except Exception as e:
            self.progress.emit(str(e))
            self.finished_job.emit(False)

    def stop(self):
        if self.proc:
            self.proc.terminate()
