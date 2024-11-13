from PySide2.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget
from .handler import demoHandler


class demo(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.button_start = QPushButton("Start Task")
        self.button_stop = QPushButton("Stop Task")  # 停止按钮
        self.status_label = QLabel("Status: Ready")
        layout.addWidget(self.button_start)
        layout.addWidget(self.button_stop)
        layout.addWidget(self.status_label)
        self.handler = demoHandler(self)