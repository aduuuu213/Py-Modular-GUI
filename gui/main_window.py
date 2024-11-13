
from dataclasses import dataclass
from typing import Dict, Optional

from PySide2.QtWidgets import (QCheckBox, QComboBox, QLineEdit, QMainWindow,
                               QRadioButton, QSpinBox, QVBoxLayout, QWidget)

from constants.config import WindowConstants
from gui.log_frame import LogFrame
from gui.menu_bar import MenuBuilder
from gui.plugin_manager import PluginArea, PluginManager
# from ui.son_widget import SonWidget  # 导入转换后的类
from utils.logger_manager import logger_manager


@dataclass
class WindowConfig:
    """窗口配置数据类"""
    width: int = WindowConstants.DEFAULT_WIDTH
    height: int = WindowConstants.DEFAULT_HEIGHT
    title: str = WindowConstants.DEFAULT_TITLE
    original_height: int = WindowConstants.DEFAULT_HEIGHT
    min_height: int = WindowConstants.MIN_HEIGHT
    min_width: int = WindowConstants.MIN_WIDTH


class ConfigHandler:
    """配置处理类"""
    @staticmethod
    def process_widget(widget: QWidget, load_data: Optional[Dict] = None, save_data: Optional[Dict] = None, widget_name: str = '') -> Dict:
        handlers = {
            QLineEdit: ConfigHandler._handle_line_edit,
            QCheckBox: ConfigHandler._handle_checkbox,
            QRadioButton: ConfigHandler._handle_radio,
            QComboBox: ConfigHandler._handle_combobox,
            QSpinBox: ConfigHandler._handle_spinbox
        }
        
        for widget_type, handler in handlers.items():
            if isinstance(widget, widget_type):
                return handler(widget, load_data, save_data, widget_name)
        return save_data or {}

    @staticmethod
    def _handle_line_edit(widget: QLineEdit, load_data: Optional[Dict], save_data: Optional[Dict], name: str) -> Dict:
        if load_data is not None:
            widget.setText(str(load_data.get(name, '')))
        elif save_data is not None:
            save_data[name] = widget.text()
        return save_data or {}

    @staticmethod
    def _handle_checkbox(widget: QCheckBox, load_data: Optional[Dict], save_data: Optional[Dict], name: str) -> Dict:
        if load_data is not None:
            widget.setChecked(load_data.get(name, False))
        elif save_data is not None:
            save_data[name] = widget.isChecked()
        return save_data or {}

    @staticmethod
    def _handle_radio(widget: QRadioButton, load_data: Optional[Dict], save_data: Optional[Dict], name: str) -> Dict:
        if load_data is not None:
            widget.setChecked(load_data.get(name, False))
        elif save_data is not None:
            save_data[name] = widget.isChecked()
        return save_data or {}

    @staticmethod
    def _handle_combobox(widget: QComboBox, load_data: Optional[Dict], save_data: Optional[Dict], name: str) -> Dict:
        if load_data is not None:
            index = load_data.get(name, 0)
            widget.setCurrentIndex(index)
        elif save_data is not None:
            save_data[name] = widget.currentIndex()
        return save_data or {}

    @staticmethod
    def _handle_spinbox(widget: QSpinBox, load_data: Optional[Dict], save_data: Optional[Dict], name: str) -> Dict:
        if load_data is not None:
            widget.setValue(load_data.get(name, widget.minimum()))
        elif save_data is not None:
            save_data[name] = widget.value()
        return save_data or {}


class MainWindow(QMainWindow):
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.config = self._load_window_config()
        self.log_show = 'true'
        # 初始化界面
        self._init_window()
        # 初始化日志控件
        self._init_widgets()
        logger_manager.setup(self.log_frame)
        # 初始化插件
        self.plugin_area = PluginArea()
        self.plugin_manager = PluginManager('plugins')
        self.plugin_manager.load_plugins()
        self._init_plugins()
        # # 构建菜单
        self.create_menu_bar()
        self.main_layout.addWidget(self.plugin_area)
        # # 加载配置
        self.load_config()
        # 检查并应用待更新的插件

    def _load_window_config(self) -> WindowConfig:
        """加载窗口配置"""
        return WindowConfig(
            width=int(self.config_manager.get('window', 'width', WindowConstants.DEFAULT_WIDTH)),
            height=int(self.config_manager.get('window', 'height', WindowConstants.DEFAULT_HEIGHT)),
            title=self.config_manager.get('window', 'title', WindowConstants.DEFAULT_TITLE),
            original_height=int(self.config_manager.get('window', 'original_height', WindowConstants.DEFAULT_HEIGHT)),
            min_height=int(self.config_manager.get('window', 'min_height', WindowConstants.MIN_HEIGHT)),
            min_width=int(self.config_manager.get('window', 'min_width', WindowConstants.MIN_WIDTH))
        )

    def _init_window(self):
        """初始化窗口属性"""
        self.setWindowTitle(self.config.title)
        self.resize(self.config.width, self.config.height)
        self.setMinimumSize(self.config.min_width, self.config.min_height)
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        # self.main_layout.setSpacing(10)

    def _init_plugins(self):
        # 检查更新信息
        pass

    def _init_widgets(self):
        self.log_frame = LogFrame()
        self.log_frame.setVisible(True)  # 默认显示
        self.main_layout.addWidget(self.log_frame)  # 添加 log_frame 到主窗口

    def load_config(self):
        # 加载日志级别
        self.file_log_level = self.config_manager.get('log', 'file_level', 'info')
        self.frame_log_level = self.config_manager.get('log', 'frame_level', 'info')
        logger_manager.set_file_level(self.file_log_level)  # 使用全局 logger_manager
        logger_manager.set_frame_level(self.frame_log_level)  # 使用全局 logger_manager
        
        # 加载其他配置
        saved_data = self.config_manager.load_all()
        self._process_widgets(self, load_data=saved_data)

    def save_config(self):
        # 保存日志级别
        self.config_manager.set('log', 'file_level', self.file_log_level)
        self.config_manager.set('log', 'frame_level', self.frame_log_level)
        self.config_manager.set('window', 'height', self.height())
        self.config_manager.set('window', 'width', self.width())
        # 保存其他配置
        save_data = {}
        save_data = self._process_widgets(self, save_data=save_data)
        self.config_manager.save_all(save_data)

    def _process_widgets(self, parent, load_data=None, save_data=None, prefix=''):
        """递归处理所有控件"""
        save_data = save_data or {}
        for child in parent.findChildren(QWidget):
            widget_name = child.objectName()
            if not widget_name:
                continue
            # 获取插件名称
            plugin_name = ''
            if hasattr(child, 'parent'):
                parent_widget = child.parent()
                while parent_widget:
                    if hasattr(parent_widget, 'plugin_name'):
                        plugin_name = parent_widget.plugin_name
                        break
                    parent_widget = parent_widget.parent()
                    
            full_name = f"{plugin_name}.{widget_name}" if plugin_name else widget_name
            # 使用 ConfigHandler 处理控件
            ConfigHandler.process_widget(child, load_data, save_data, full_name)
            # 递归处理子控件
            if hasattr(child, 'layout'):
                new_prefix = f"{full_name}." if widget_name else prefix
                self._process_widgets(child, load_data, save_data, new_prefix)

        return save_data

    def closeEvent(self, event):
        self.save_config()
        super().closeEvent(event)

    # MainWindow 类中添加新方法
    def create_menu_bar(self):
        MenuBuilder(self).build_all_menus()

    def clear_config(self):
        """清空所有控件的值"""
        self._process_widgets(self, load_data={})