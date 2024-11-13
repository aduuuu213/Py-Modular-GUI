# -*- coding: utf-8 -*-
from threading import Event, Thread
from dataclasses import dataclass
from typing import Optional, List, Tuple, Union
from enum import Enum

from .worker import create_apply_text, handle_apply, login_by_token, main_process
from PySide2.QtCore import Slot, Qt
from PySide2.QtGui import QColor, QPalette, QIntValidator
from PySide2.QtWidgets import (QComboBox, QGridLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QVBoxLayout, QWidget)
from utils.logger_manager import logger_manager


CONTAINER_TYPE_LIST = [
        {"ctnType": "20BULK"},
        {"ctnType": "20BULK(high)"},
        {"ctnType": "20DRY"},
        {"ctnType": "20FLAT"},
        {"ctnType": "20HIGH"},
        {"ctnType": "20HIVE"},
        {"ctnType": "20OPEN"},
        {"ctnType": "20OPEN(high)"},
        {"ctnType": "20OSOT"},
        {"ctnType": "20PLWD"},
        {"ctnType": "20PORT"},
        {"ctnType": "20REEF"},
        {"ctnType": "20RH"},
        {"ctnType": "20TANK"},
        {"ctnType": "20TANK(8)"},
        {"ctnType": "40DRY"},
        {"ctnType": "40FLAT"},
        {"ctnType": "40FLAT(high)"},
        {"ctnType": "40HCRF"},
        {"ctnType": "40HIGH"},
        {"ctnType": "40OPEN"},
        {"ctnType": "40OPEN(high)"},
        {"ctnType": "40PLWD"},
        {"ctnType": "40PLWD(high)"},
        {"ctnType": "40REEF"},
        {"ctnType": "40TANK"},
        {"ctnType": "40TANK(high)"},
        {"ctnType": "40TK"},
        {"ctnType": "40TWDK"},
        {"ctnType": "45HCRF"},
        {"ctnType": "45HIGH"},
        {"ctnType": "45PLWD(high)"},
]


class RegionType(Enum):
    NONE = "不选区域"
    LUCHAOGANG = "芦潮港区域"
    WAIGAOQIAO = "外高桥区域"

@dataclass
class GridCell:
    label: QLabel
    line_edit: QLineEdit
    layout: QHBoxLayout

class msk(QWidget):
    GRID_SIZE = (6, 4)
    BUTTON_SIZE = (80, 30)
    
    def __init__(self):
        super().__init__()
        self.logger = logger_manager.logger
        self.stop_event = Event()
        self.worker_thread: Optional[Thread] = None
        self.grid_cells: List[List[GridCell]] = []
        
        self._init_ui()
    
    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.addLayout(self._create_grid_layout())
        main_layout.addLayout(self._create_control_panel())
        main_layout.addLayout(self._create_delay_panel())
        main_layout.setSpacing(10)
        self.setLayout(main_layout)
    
    def _create_delay_panel(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)
        
        # 添加服务初始化相关控件
        token_input = QLineEdit(objectName="token")
        layout.addWidget(QPushButton("服务初始化", clicked=lambda: self._validate_and_login(token_input)))
        layout.addWidget(QLabel("token"))
        layout.addWidget(token_input, 1)  # 1 表示 stretch
        
        layout.addWidget(QLabel("随机延迟小"))
        
        # 创建 QLineEdit 后单独设置验证器
        delay_min = QLineEdit(objectName='delay_min')
        delay_min.setValidator(QIntValidator(bottom=0, top=100))
        layout.addWidget(delay_min)
        
        layout.addWidget(QLabel("随机延迟大"))
        
        # 创建 QLineEdit 后单独设置验证器
        delay_max = QLineEdit(objectName='delay_max')
        delay_max.setValidator(QIntValidator(bottom=0, top=100))
        layout.addWidget(delay_max)
        
        layout.addWidget(QPushButton("测试音乐", clicked=lambda: self._test_play_music()))
        return layout
    
    def _create_grid_layout(self) -> QGridLayout:
        layout = QGridLayout()
        layout.setSpacing(10)
        
        for row in range(self.GRID_SIZE[0]):
            row_cells = []
            for col in range(self.GRID_SIZE[1]):
                cell = self._create_grid_cell(row, col)
                layout.addLayout(cell.layout, row, col)
                row_cells.append(cell)
            self.grid_cells.append(row_cells)
            
        return layout

    def _create_grid_cell(self, row: int, col: int) -> GridCell:
        layout = QHBoxLayout()
        label = self._create_status_label(row, col)
        line_edit = self._create_input_field(row, col)
        
        layout.addWidget(label)
        layout.addWidget(line_edit)
        layout.setSpacing(0)
        
        return GridCell(label=label, line_edit=line_edit, layout=layout)

    def _create_status_label(self, row: int, col: int) -> QLabel:
        label = QLabel()
        label.setFixedSize(20, 20)
        label.setObjectName(f"label_{row}_{col}")
        label.setAutoFillBackground(True)
        
        # palette = QPalette()
        # palette.setColor(QPalette.Window, QColor("red"))
        # label.setPalette(palette)
        label.setStyleSheet("background-color: red;")
        label.mousePressEvent = lambda event: self._handle_label_click(label)
        return label
        
    def _handle_label_click(self, label: QLabel):
        """处理标签点击事件"""
        _, row, col = label.objectName().split('_')
        line_edit = self.grid_cells[int(row)][int(col)].line_edit
        # print(label.palette().color(QPalette.Window))
        # print(QColor("red"))
        if (label.palette().color(QPalette.Window) == QColor("red") and 
            line_edit.text().strip()):
            self._update_label_status(label, handle_apply(line_edit.text().strip()))
        else:
            self.show_message("提示", "不能手动操作")
            
    def _update_label_status(self, label: QLabel, success: bool):
        """更新标签状态"""
        color = "#4CAF50" if success else "#FF0000"
        label.setStyleSheet(f"background-color: {color};")

    def _create_input_field(self, row: int, col: int) -> QLineEdit:
        line_edit = QLineEdit()
        line_edit.setObjectName(f"line_edit_{row}_{col}")
        return line_edit

    def _create_control_panel(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(10)
        
        # 初始化控件
        self.bill_id = QLineEdit()
        self.ctnr_count = QLineEdit()
        self.ctnr_type = self._create_container_type_selector()
        self.region = self._create_region_selector()
        
        # 添加操作按钮
        layout.addWidget(QPushButton("循环_开始", clicked=self.start_process))
        layout.addWidget(QPushButton("循环_结束", clicked=self.stop_process))
        
        # 添加输入字段
        fields = [
            ("订舱号", self.bill_id),
            ("箱数", self.ctnr_count),
            ("箱型", self.ctnr_type),
            ("区域", self.region)
        ]
        for label_text, widget in fields:
            layout.addWidget(QLabel(label_text))
            layout.addWidget(widget)
            
        layout.addWidget(QPushButton("生成", clicked=lambda: create_apply_text(self)))
        return layout

    def _create_region_selector(self) -> QComboBox:
        combo_box = QComboBox()
        for region in ["不选区域", "芦潮港区域", "外高桥区域"]:
            combo_box.addItem(region)
        return combo_box

    def _create_container_type_selector(self) -> QComboBox:  # 新增方法
        combo_box = QComboBox()
        # 添加箱型选项
        for item in CONTAINER_TYPE_LIST:
            combo_box.addItem(item['ctnType'])
        return combo_box
    
    def start_process(self):
        if self.worker_thread and self.worker_thread.is_alive():
            self.logger('正在运行中')
            return
        self.stop_event.clear()  # 重置事件状态
        self.worker_thread = Thread(target=lambda: main_process(self))
        self.worker_thread.daemon = True
        self.worker_thread.start()
        self.logger.info('主线程启动')
    
    def stop_process(self):
        if self.worker_thread:
            self.logger.info('点击停止')
            self.stop_event.set()  # 设置停止信号
            self.worker_thread.join()  # 等待线程结束
            self.logger.info("主线程已停止")
        else:
            self.logger.info("主线程未启动")
    
    @Slot(str, str)
    def show_message(self, title, message):
        from PySide2.QtWidgets import QMessageBox
        QMessageBox.information(self, title, message)
    
    def find_QLineEdit(self):
        for row in range(self.GRID_SIZE[0]):
            for col in range(self.GRID_SIZE[1]):
                line_edit = self.findChild(QLineEdit, f"line_edit_{row}_{col}")
                if line_edit and not line_edit.text():
                    return line_edit
        return None

    def show_selection_dialog(self, items):
        from PySide2.QtWidgets import (QComboBox, QDialog, QHBoxLayout,
                                       QVBoxLayout)

        dialog = QDialog(self)
        dialog.setWindowTitle("选择")
        layout = QVBoxLayout()
        
        combo = QComboBox()
        combo.addItems(items)
        layout.addWidget(combo)
        
        btn_layout = QHBoxLayout()
        confirm_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        
        btn_layout.addWidget(confirm_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        
        result = [-1]  # 用列表存储结果，以便在内部函数中修改
        
        confirm_btn.clicked.connect(lambda: result.__setitem__(0, combo.currentIndex()) or dialog.accept())
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec_()
        return result[0]

    def _validate_and_login(self, token_input):
        if not token_input.text().strip():
            self.show_message("错误", "请填写token")
            return
        login_by_token(token_input.text())
    
    def add_widgets(self, layout: QHBoxLayout, widgets: List[Union[QWidget, Tuple[QWidget, int]]]):
        """Helper method to add widgets to layout with optional stretch"""
        for widget in widgets:
            if isinstance(widget, tuple):
                layout.addWidget(widget[0], stretch=widget[1])
            else:
                layout.addWidget(widget)
                
    def _test_play_music(self):
        from playsound import playsound
        from playsound import PlaysoundException
        from threading import Thread

        def play_sound():
            try:
                playsound("resources/ring.mp3")  # 替换为你的音乐文件路径
            except PlaysoundException as e:
                self.show_message("错误", f"{e}")

        Thread(target=play_sound).start()
