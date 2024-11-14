from queue import Queue

from PySide2.QtCore import QTimer
from PySide2.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget
from utils.logger_manager import logger_manager

class LogFrame(QWidget):
    def __init__(self):
        super().__init__()
        self.max_lines = 100
        self.create_widgets()

    def create_widgets(self):
        layout = QVBoxLayout(self)
        
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: black; color: green;")
        # self.log_text.setMinimumHeight(300)  # 设置最小高度为100像素
        layout.addWidget(self.log_text)
        
        self.queue = Queue()
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_queue)
        self.timer.start(100)

    def check_queue(self):
        while not self.queue.empty():
            msg = self.queue.get()
            self.log_text.appendPlainText(msg)
            
            # 优化：批量删除超出行数
            if self.log_text.blockCount() > self.max_lines:
                cursor = self.log_text.textCursor()
                cursor.movePosition(cursor.Start)
                cursor.movePosition(cursor.Down, cursor.KeepAnchor, 
                                  self.log_text.blockCount() - self.max_lines)
                cursor.removeSelectedText()
            
            # 滚动到底部
            self.log_text.verticalScrollBar().setValue(
                self.log_text.verticalScrollBar().maximum()
            )

    def write(self, msg):
        self.queue.put(msg)