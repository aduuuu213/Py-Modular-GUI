from pathlib import Path

from PySide2.QtCore import QUrl
from PySide2.QtGui import QDesktopServices
from PySide2.QtWidgets import QAction, QActionGroup, QMenu, QMessageBox

from constants.config import WindowConstants
from utils.logger_manager import logger_manager
from utils.messages import show_message


# 新增 MenuBuilder 类来处理菜单创建
class MenuBuilder:
    """菜单构建器"""
    def __init__(self, window):
        self.window = window
        self.menubar = window.menuBar()
        self.log_show = window.log_show
        self.log_frame = window.log_frame
        self.config = window.config
        self.config_manager = window.config_manager

    def build_all_menus(self):
        """构建所有菜单"""
        self.build_config_menu()
        self.build_log_menu()
        # 构建样式菜单
        self.build_style_menu()  # 新增
        # 构建插件菜单
        self.build_plugin_menu()
        # 构建帮助菜单
        self.build_help_menu()
    
    def build_plugin_menu(self):
        """构建插件菜单"""
        plugin_menu = self.menubar.addMenu('插件')
        plugin_names = self.window.plugin_manager.get_plugin_names()
        for plugin_name in plugin_names:
            plugin_alias = self.window.plugin_manager.get_plugin_alias(plugin_name)
            action = QAction(plugin_alias, self.window, objectName=plugin_name)
            action.setCheckable(True)
            # 获取插件显示状态
            status = self.config_manager.get('plugins', plugin_name, 'false')
            if status.lower() == 'true':
                self.window.plugin_area.add_plugin(self.window.plugin_manager.get_plugin(plugin_name))
            action.setChecked(status.lower() == 'true')
            action.triggered.connect(lambda checked=(status.lower() == 'true'), name=plugin_name: self.toggle_plugin(name, checked))
            plugin_menu.addAction(action)
        # 添加版本检查菜单项
        plugin_menu.addSeparator()
        version_action = QAction('插件管理', self.window)
        version_action.triggered.connect(self.show_version_dialog)
        plugin_menu.addAction(version_action)

    def build_help_menu(self):
        """构建帮助菜单"""
        help_menu = self.menubar.addMenu('帮助')
        # 添加关于菜单项
        git_action = QAction('Github', self.window)
        git_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/aduuuu213/Py-Modular-GUI")))
        help_menu.addAction(git_action)
        about_action = QAction('关于', self.window)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def build_log_menu(self):
        """构建日志菜单"""
        log_menu = self.menubar.addMenu('日志')
        
        # 显示/隐藏日志框
        show_log_action = QAction('显示日志框', self.window)
        show_log_action.setCheckable(True)
        show_log_action.setChecked(self.log_show.lower() == 'true')
        show_log_action.triggered.connect(self.toggle_log_frame)
        log_menu.addAction(show_log_action)
        
        # 日志级别子菜单
        self._build_log_level_menu(log_menu)
        
        # 日志框大小调节
        self._build_log_size_menu(log_menu)

    def _build_log_level_menu(self, parent_menu: QMenu):
        """构建日志级别子菜单"""
        # 获取当前日志级别
        current_file_level = self.config_manager.get('log', 'file_level', 'info')
        current_frame_level = self.config_manager.get('log', 'frame_level', 'info')

        # 文件日志级别
        file_menu = QMenu('文件日志级别', self.window)
        file_group = QActionGroup(self.window, objectName='file_group')  # 创建互斥动作组
        for level in ['debug', 'info']:
            action = QAction(level, self.window)
            action.setCheckable(True)
            action.setChecked(level == current_file_level)  # 设置初始选中状态
            action.triggered.connect(lambda: self.create_file_log_handler(level))  # 使用闭包
            file_group.addAction(action)  # 添加到互斥组
            file_menu.addAction(action)
        parent_menu.addMenu(file_menu)

        # 界面日志级别
        frame_menu = QMenu('界面日志级别', self.window)
        frame_group = QActionGroup(self.window, objectName='frame_group')  # 创建互斥动作组
        for level in ['debug', 'info']:
            action = QAction(level, self.window)
            action.setCheckable(True)
            action.setChecked(level == current_frame_level)  # 设置初始选中状态
            action.triggered.connect(lambda: self.create_frame_log_handler(level))  # 使用闭包
            frame_group.addAction(action)  # 添加到互斥组
            frame_menu.addAction(action)
        parent_menu.addMenu(frame_menu)

    def create_file_log_handler(self, level):
        """创建文件日志级别触发处理函数"""
        file_group = self.window.findChild(QActionGroup, 'file_group')
        selected_action = file_group.checkedAction()  # 获取当前选中的动作
        level = selected_action.text() if selected_action else 'info'
        return self.set_file_log_level(level)

    def create_frame_log_handler(self, level):
        """创建界面日志级别触发处理函数"""
        frame_group = self.window.findChild(QActionGroup, 'frame_group')
        selected_action = frame_group.checkedAction()  # 获取当前选中的动作
        level = selected_action.text() if selected_action else 'info'
        return self.set_frame_log_level(level)

    def _build_log_size_menu(self, parent_menu: QMenu):
        """构建日志大小调节菜单"""
        parent_menu.addSeparator()
        
        increase_action = QAction('增加日志框高度', self.window)
        increase_action.setShortcut('Ctrl+=')
        increase_action.triggered.connect(self.increase_log_height)
        
        decrease_action = QAction('减少日志框高度', self.window)
        decrease_action.setShortcut('Ctrl+-')
        decrease_action.triggered.connect(self.decrease_log_height)
        
        parent_menu.addAction(increase_action)
        parent_menu.addAction(decrease_action)
        
    def build_style_menu(self):
        """构建样式菜单"""
        style_menu = self.menubar.addMenu('样式')
        style_group = QActionGroup(self.window, objectName='style_group')  # 创建互斥动作组
        
        # 获取当前样式
        current_style = self.config_manager.get('window', 'style', 'default')
        
        # 添加默认样式
        default_action = QAction('default', self.window)
        default_action.setCheckable(True)
        default_action.setChecked(current_style == 'default')
        default_action.triggered.connect(lambda: self.change_style('default'))
        style_group.addAction(default_action)
        style_menu.addAction(default_action)
        
        # 遍历 resources/qss 目录下的样式文件
        qss_dir = Path('resources/qss')
        if qss_dir.exists():
            for qss_file in qss_dir.glob('*.qss'):
                style_name = qss_file.stem
                action = QAction(style_name, self.window)
                action.setCheckable(True)
                action.setChecked(current_style == style_name)
                action.triggered.connect(lambda: self.change_style('style'))
                style_group.addAction(action)
                style_menu.addAction(action)
        # 初始加载
        self.change_style('default')

    def build_config_menu(self):
        config_menu = self.menubar.addMenu('配置')
        actions = {
            '保存': self.window.save_config,
            '读取': self.window.load_config,
            '清空': self.window.clear_config
        }
        for name, handler in actions.items():
            action = QAction(name, self.window)
            action.triggered.connect(handler)
            config_menu.addAction(action)
        return config_menu

    def show_about(self):
        disclaimer = (
            "免责声明：\n\n"
            "1. 本软件框架仅供学习和测试目的，使用者需确保其使用符合当地法律法规。\n"
            "2. 严禁将本软件框架用于任何非法用途，包括但不限于数据盗取、网络攻击、破坏计算机系统等行为。\n"
            "3. 本软件框架不对用户开发或使用的插件内容负责，使用者应自行承担因插件使用而产生的所有法律后果。\n"
            "4. 本软件框架按“现状”提供，作者不对其功能、性能或适用性作出任何明示或暗示的保证。\n"
            "5. 使用本软件框架即表示您同意本免责声明的所有条款，并承诺遵守相关法律法规。\n"
            "6. 本免责声明的条款如有变更，恕不另行通知，建议用户定期查阅。\n"
            "7. 如您不同意本免责声明的任何条款，请立即停止使用本软件框架。\n"
            "8. 本软件框架为免费提供，作者不对框架的使用、修改或分发承担任何责任。\n"
            "9. 使用者应对其行为负责，因使用本软件框架及其插件进行任何违法行为所产生的法律责任，均由使用者自行承担。\n"
        )
        QMessageBox.about(self.window, "关于", disclaimer)

    def toggle_log_frame(self):
        """切换日志框显示状态"""
        is_visible = not self.log_frame.isVisible()
        self.log_show = str(is_visible)
        self.log_frame.setVisible(is_visible)
        if is_visible:
            self.window.resize(self.window.width(), self.config.original_height)
        else:
            hight = self.config.original_height - self.log_frame.height()
            if hight < self.config.min_height:
                hight = self.config.min_height
            self.window.resize(self.window.width(), hight)

    def increase_log_height(self):
        """增加日志框高度"""
        if self.log_frame.isVisible():
            current_height = self.log_frame.height()
            if current_height < WindowConstants.MAX_LOG_HEIGHT: 
                new_height = current_height + WindowConstants.LOG_HEIGHT_STEP  # 每次增加50像素
                self.log_frame.setFixedHeight(new_height)
                self.window.resize(self.window.width(), self.window.height() + WindowConstants.LOG_HEIGHT_STEP)
                self.config.original_height += WindowConstants.LOG_HEIGHT_STEP
            else:
                show_message(self.window, "失败", "最大了")
        else:
            show_message(self.window, "失败", "未显示日志框")

    def decrease_log_height(self):
        """减少日志框高度"""
        if self.log_frame.isVisible():
            current_height = self.log_frame.height()
            if current_height > WindowConstants.MIN_LOG_HEIGHT:  # 设置最小高度限制
                new_height = current_height - WindowConstants.LOG_HEIGHT_STEP  # 每次减少50像素
                self.log_frame.setFixedHeight(new_height)
                self.window.resize(self.window.width(), self.window.height() - WindowConstants.LOG_HEIGHT_STEP)
                self.config.original_height -= WindowConstants.LOG_HEIGHT_STEP
            else:
                show_message(self.window, "失败", "最小了")
        else:
            show_message(self.window, "失败", "未显示日志框")

    def set_file_log_level(self, level):
        """设置文件日志级别"""
        self.window.file_log_level = level
        logger_manager.set_file_level(level)
        logger_manager.logger.info(f'设置文件日志级别: {level}')

    def set_frame_log_level(self, level):
        """设置界面日志级别"""
        self.window.frame_log_level = level
        logger_manager.set_frame_level(level)
        logger_manager.logger.info(f'设置界面日志级别: {level}')

    def change_style(self, style_name):
        """切换样式"""
        style_group = self.window.findChild(QActionGroup, 'style_group')
        selected_action = style_group.checkedAction()  # 获取当前选中的动作
        style_name = selected_action.text() if selected_action else 'default'  # 获取样式名称
        logger_manager.logger.info(f'切换样式: {style_name}')
        if style_name == 'default':
            self.window.setStyleSheet('')
        else:
            qss_path = Path(f'resources/qss/{style_name}.qss')
            if qss_path.exists():
                with open(qss_path, 'r', encoding='utf-8') as f:
                    self.window.setStyleSheet(f.read())
        # 保存样式设置
        self.config_manager.set('window', 'style', style_name)

    def show_version_dialog(self):
        """显示版本检查对话框"""
        from .version_dialog import VersionDialog
        dialog = VersionDialog(self.window.plugin_manager, self.window)
        dialog.exec_()

    def toggle_plugin(self, name, checked):
        """切换插件状态"""
        print(name)
        action = self.window.findChild(QAction, name)
        checked = action.isChecked()
        self.config_manager.set('plugins', name, str(checked).lower())
        print(self.config_manager.get('plugins', name))
        if checked:
            self.window.plugin_area.add_plugin(self.window.plugin_manager.get_plugin(name))
        else:
            self.window.plugin_area.remove_plugin(self.window.plugin_manager.get_plugin(name))