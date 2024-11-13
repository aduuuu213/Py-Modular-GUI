import logging
import sys
from typing import Optional
from PySide2.QtCore import QObject, Signal

class LogSignal(QObject):
    """用于发送日志信号的QT对象"""
    log_signal = Signal(str)

class UIHandler(logging.Handler):
    def __init__(self, ui_component):
        super().__init__()
        self.ui_component = ui_component
        self.log_signal = LogSignal()
        self.log_signal.log_signal.connect(self.ui_component.write)

    def emit(self, record):
        log_entry = self.format(record)
        self.log_signal.log_signal.emit(log_entry)

class LoggerManager:
    _instance: Optional['LoggerManager'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._logger = None
            self._ui_component = None
            self.file_log_level = 'info'
            self.frame_log_level = 'info'
            self.file_handler = None
            self.ui_handler = None
            self.console_handler = None
    
    def setup(self, ui_component=None):
        """初始化日志系统"""
        if self._logger is not None:
            return self._logger
            
        self._ui_component = ui_component
        self._logger = logging.getLogger('app_logger')
        self._logger.setLevel(logging.DEBUG)
        
        # 文件处理器
        self.file_handler = logging.FileHandler('logs/app.log', encoding='utf-8')
        self.file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器
        self.console_handler = logging.StreamHandler(sys.stdout)
        self.console_handler.setLevel(logging.DEBUG)
        
        # 格式化器
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        self.file_handler.setFormatter(formatter)
        self.console_handler.setFormatter(formatter)
        
        self._logger.addHandler(self.file_handler)
        self._logger.addHandler(self.console_handler)
        
        # UI处理器
        if ui_component:
            self.ui_handler = UIHandler(ui_component)
            self.ui_handler.setFormatter(formatter)
            self.ui_handler.setLevel(logging.INFO)  # 设置UI显示的最低日志级别为INFO
            self._logger.addHandler(self.ui_handler)
        return self._logger
    
    def set_file_level(self, level: str):
        """设置文件日志级别"""
        if self.file_handler:  # 检查文件处理器是否存在
            self.file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    def set_frame_level(self, level: str):
        """设置界面日志级别"""
        if self.ui_handler:  # 检查UI处理器是否存在
            # print(level)
            self.ui_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        
    @property
    def logger(self):
        """获取logger实例"""
        if self._logger is None:
            self._logger = self.setup()
        return self._logger

# 全局单例
logger_manager = LoggerManager() 