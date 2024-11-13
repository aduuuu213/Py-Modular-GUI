from .worker import demoWorker
from PySide2.QtCore import QObject, Signal

class demoHandler(QObject):
    update_status_signal = Signal(str)

    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.worker = demoWorker()
        self.worker.finished.connect(self.on_task_finished)
        self.worker.progress.connect(self.update_progress)

        self.ui.button_start.clicked.connect(self.start_task)
        self.ui.button_stop.clicked.connect(self.stop_task)  # 停止按钮

    def start_task(self):
        self.update_status_signal.emit("Status: Running...")
        self.worker._running = True
        self.worker.start()  # 启动工作线程

    def stop_task(self):
        self.worker.stop()  # 停止工作线程
        self.update_status_signal.emit("Status: Stopped")

    def on_task_finished(self):
        self.update_status_signal.emit("Status: Finished")

    def update_progress(self, status):
        self.ui.status_label.setText(status)
