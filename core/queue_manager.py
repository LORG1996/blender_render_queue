from PySide6.QtCore import QObject, Signal

class QueueManager(QObject):
    status_changed = Signal()

    def __init__(self):
        super().__init__()
        self.tasks = []

    def add(self, task):
        self.tasks.append(task)
        self.status_changed.emit()

    def remove(self, idx):
        if 0 <= idx < len(self.tasks):
            del self.tasks[idx]
            self.status_changed.emit()

    def move(self, i, j):
        if 0 <= i < len(self.tasks) and 0 <= j < len(self.tasks):
            self.tasks.insert(j, self.tasks.pop(i))
            self.status_changed.emit()

    def move_up(self, i):
        if i > 0:
            self.move(i, i-1)

    def move_down(self, i):
        if i < len(self.tasks) - 1:
            self.move(i, i+1)

    def duplicate(self, i):
        if 0 <= i < len(self.tasks):
            self.tasks.append(dict(self.tasks[i]))
            self.status_changed.emit()

    def clear(self):
        self.tasks.clear()
        self.status_changed.emit()
