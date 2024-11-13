import time

from PySide2.QtCore import QThread, Signal
from utils.logger_manager import logger_manager


class demoWorker(QThread):
    finished = Signal()  # 用于发射任务完成信号
    progress = Signal(str)  # 用于更新进度信息
    
    def __init__(self):
        super().__init__()
        self._running = False  # 线程运行标志
        self.logger = logger_manager.logger

    def run(self):
        while self._running:
            # 模拟耗时操作
            self.logger.info("开始任务")
            time.sleep(1)  # 每秒执行一次
            self.progress.emit("Working...")  # 更新进度
        self.logger.info("任务完成")
        self.finished.emit()  # 任务完成后发出信号

    def stop(self):
        self._running = False  # 停止线程