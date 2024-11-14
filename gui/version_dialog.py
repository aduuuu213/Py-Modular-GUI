import json
import shutil
import subprocess
import sys
from pathlib import Path

from packaging import version
from PySide2.QtCore import QThread, Signal
from PySide2.QtWidgets import (QApplication, QDialog, QHeaderView,
                               QInputDialog, QMessageBox, QProgressBar,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout)

from constants.config import PIP_SOURCE, PLUGIN_DIR, PLUGIN_UPDATE_CACHE_DIR
from constants.messages import *
from utils.logger_manager import logger_manager
from utils.requests import download_file, get_json


def _get_python_path():
    python_path = sys.executable
    if python_path.endswith('python.exe'):
        # 开发环境返回 python.exe 路径
        return python_path
    # 生产环境返回 .\runtime\python.exe 路径
    return r'.\runtime\python.exe'

def check_package_installed(package_name, version=""):
    """检查指定的包是否已安装并且版本匹配"""
    try:
        # 使用 pip 检查包是否已安装
        logger_manager.logger.info(_get_python_path())
        result = subprocess.run(
            [_get_python_path(), '-m', 'pip', 'show', package_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            # 解析版本信息
            for line in result.stdout.splitlines():
                if line.startswith('Version:'):
                    installed_version = line.split(' ')[1]
                    if version:  # 检查版本是否为空
                        return version.parse(installed_version) >= version.parse(version)  # 修改为大于等于
                    return True  # 如果版本为空，返回 True 跳过检测
        return False
    except Exception as e:
        logger_manager.logger.error(f"检查包安装时发生错误: {e}")
        return False

def install_package(package_name, version=""):
    """使用 pip 安装指定的包和版本"""
    try:
        if version:
            subprocess.run([_get_python_path(), '-m', 'pip', 'install', f"{package_name}>={version}", '--index-url', PIP_SOURCE], check=True)
        else:
            subprocess.run([_get_python_path(), '-m', 'pip', 'install', package_name, '--index-url', PIP_SOURCE], check=True)
        logger_manager.logger.info(f"成功安装包: {package_name}>={version}")
    except subprocess.CalledProcessError as e:
        logger_manager.logger.error(f"安装包时发生错误: {e}")

class VersionDialog(QDialog):
    def __init__(self, plugin_manager, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self.window = parent
        self.setWindowTitle("插件版本信息")
        self.resize(600, 400)

        layout = QVBoxLayout(self)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)  # 增加状态和更新地址列
        self.table.setHorizontalHeaderLabels(["插件名称", "当前版本", "最新版本", "状态", "描述"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # 添加检查按钮
        self.check_button = QPushButton("检查更新")
        self.check_button.clicked.connect(self.check_updates)
        
        # 添加更新按钮
        self.update_button = QPushButton("更新选中插件")
        self.update_button.clicked.connect(self.update_selected_plugins)
        self.update_button.setEnabled(False)

        # 添加卸载按钮
        # self.uninstall_button = QPushButton("卸载选中插件")
        # self.uninstall_button.clicked.connect(self.uninstall_selected_plugins)
        # self.uninstall_button.setEnabled(False)

        # 添加在线安装按钮
        self.online_install_button = QPushButton("在线安装")
        self.online_install_button.clicked.connect(self.online_install_plugins)
        
        layout.addWidget(self.online_install_button)
        layout.addWidget(self.table)
        layout.addWidget(self.check_button)
        layout.addWidget(self.update_button)
        # layout.addWidget(self.uninstall_button)  # 添加卸载按钮
        
        # 允许选择行
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
        self.table.itemSelectionChanged.connect(self._handle_selection)
        
        # 填充插件信息
        self._fill_plugin_info()
        
    def _fill_plugin_info(self):
        plugins = self.plugin_manager.get_plugin_info_list()
        self.table.setRowCount(len(plugins))
        
        for row, plugin in enumerate(plugins):
            self.table.setItem(row, 0, QTableWidgetItem(plugin.get('name', '')))
            self.table.setItem(row, 1, QTableWidgetItem(plugin.get('version', '')))
            self.table.setItem(row, 2, QTableWidgetItem('-'))
            self.table.setItem(row, 3, QTableWidgetItem('-'))
            self.table.setItem(row, 4, QTableWidgetItem(plugin.get('description', '')))
    
    def check_updates(self):
        """检查插件更新"""
        plugins = self.plugin_manager.get_plugin_info_list()
        for row, plugin in enumerate(plugins):
            try:
                if 'update_url' not in plugin:
                    self._update_status(row, '-', '未配置更新地址')
                    continue
                    
                # 获取在线版本信息
                response_json = get_json(plugin['update_url'], timeout=5)
                if not response_json:
                    self._update_status(row, '-', '检查失败')
                    continue
                    
                online_info = response_json
                if not self._validate_online_info(online_info):
                    self._update_status(row, '-', WARNING_MESSAGE_INVALID_UPDATE_INFO)
                    continue
                
                # 更新版本信息
                current_version = plugin.get('version', '0')
                latest_version = online_info.get('version', '0')
                self.table.setItem(row, 2, QTableWidgetItem(latest_version))
                if version.parse(latest_version) > version.parse(current_version):    
                    self.table.setItem(row, 3, QTableWidgetItem(WARNING_MESSAGE_NEW_VERSION_AVAILABLE))
                else:
                    self.table.setItem(row, 3, QTableWidgetItem(WARNING_MESSAGE_ALREADY_LATEST_VERSION))
            except Exception as e:
                logger_manager.logger.error(f"检查插件更新时发生错误: {e}")
                self._update_status(row, '-', '检查失败')
    
    def _update_status(self, row, status, message):
        self.table.setItem(row, 3, QTableWidgetItem(status))
        self.table.setItem(row, 4, QTableWidgetItem(message))
    
    def _validate_online_info(self, online_info):
        """验证在线版本信息的逻辑"""
        required_keys = ['version', 'download_url', 'name', 'description', 'plugin_name']
        return all(key in online_info for key in required_keys)

    def _handle_selection(self):
        """处理选择变化"""
        self.update_button.setEnabled(len(self.table.selectedItems()) > 0)
        # self.uninstall_button.setEnabled(len(self.table.selectedItems()) > 0)  # 更新卸载按钮状态

    def update_selected_plugins(self):
        """更新选中的插件"""
        selected_rows = set(item.row() for item in self.table.selectedItems())
        plugins = self.plugin_manager.get_plugin_info_list()
        
        updates = []
        for row in selected_rows:
            plugin_info = plugins[row]
            status_item = self.table.item(row, 3)
            if status_item and status_item.text() == WARNING_MESSAGE_NEW_VERSION_AVAILABLE:
                updates.append(plugin_info)

        if not updates:
            QMessageBox.information(self, "提示", "没有选中需要更新的插件")
            return

        reply = QMessageBox.question(self, '确认更新', 
                                   f'确定要更新选中的 {len(updates)} 个插件吗？\n更新后需要重启程序。',
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self._perform_updates(updates)

    def _perform_updates(self, plugins_to_update, install_plugins=False):
        """执行更新操作"""
        root_dir = Path(__file__).resolve().parent.parent
        temp_dir = root_dir / PLUGIN_UPDATE_CACHE_DIR
        temp_dir.mkdir(exist_ok=True)
        print(f"临时目录: {temp_dir}")
        
        # 创建进度条
        progress_bar = QProgressBar(self)
        progress_bar.setRange(0, len(plugins_to_update))
        progress_bar.setValue(0)
        
        layout = QVBoxLayout()
        layout.addWidget(progress_bar)
        self.setLayout(layout)  # 假设在一个 QWidget 中

        json_write = {"install_plugins": []}
        for index, plugin in enumerate(plugins_to_update):
            try:
                # 获取更新信息
                if install_plugins:
                    update_info = plugin
                else:
                    update_info = get_json(plugin['update_url'], timeout=5)
                # 下载新版本
                download_url = update_info['download_url']
                plugin_name = update_info['plugin_name']
                print(f"插件名: {plugin_name}")
                # 下载到临时目录
                temp_file = temp_dir / f"{plugin_name}_{update_info['version']}.zip"
                print(f"下载文件: {temp_file}")
                download_file(download_url, temp_file)
                json_write["install_plugins"].append({plugin_name: str(temp_file)})
            except Exception as e:
                logger_manager.logger.error(f"更新插件时发生错误: {e}")
                continue
            
            # 更新进度条
            progress_bar.setValue(index + 1)

        # 写入更新信息到配置文件
        self._write_update_info(json_write)
        
        if json_write:  # 检查 json_write 是否不为空
            reply = QMessageBox.question(self, '提示', 
                                        '更新成功，确认关闭后应用程序？',
                                        QMessageBox.StandardButton.Yes | 
                                        QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self._restart_app()
                

    def _write_update_info(self, json_write):
        """写入更新信息到配置文件"""
        logger_manager.logger.debug(f"写入更新信息: {PLUGIN_UPDATE_CACHE_DIR}/update_info.json")
        with open(f'{PLUGIN_UPDATE_CACHE_DIR}/update_info.json', 'w') as f:
            json.dump(json_write, f)

    # 新增一个线程类
    class InstallThread(QThread):
        update_progress = Signal(int)

        def __init__(self, dependencies):
            super().__init__()
            self.dependencies = dependencies

        def run(self):
            for index, (dependency, version) in enumerate(self.dependencies.items()):
                logger_manager.logger.info(f"检测依赖包: {dependency}>={version}")
                if not check_package_installed(dependency, version):
                    install_package(dependency, version)
                self.update_progress.emit(index + 1)  # 更新进度

    def online_install_plugins(self):
        """在线安装插件"""
        url, ok = QInputDialog.getText(self, '输入插件安装地址', '请输入插件的安装地址:')
        if not ok or not url:
            return

        try:
            # 获取插件元信息
            response_json = get_json(url, timeout=5)
            if not response_json:
                QMessageBox.warning(self, "警告", "获取插件信息失败")
                return

            # 展示插件信息
            plugin_name = response_json.get('name', '未知插件')
            plugin_version = response_json.get('version', '未知版本')
            plugin_description = response_json.get('description', '无描述')

            message = f"插件名称: {plugin_name}\n版本: {plugin_version}\n描述: {plugin_description}\n\n确认安装吗？"
            reply = QMessageBox.question(self, '确认安装', message,
                                        QMessageBox.StandardButton.Yes | 
                                        QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                # 检测 dependencies 是否需要安装
                dependencies = response_json.get('dependencies', {})
                if dependencies:
                    # 创建进度条
                    self.progress_bar = QProgressBar(self)
                    self.progress_bar.setRange(0, len(dependencies))  # 设置进度条范围
                    self.layout().addWidget(self.progress_bar)  # 将进度条添加到布局中
                    install_thread = self.InstallThread(dependencies)
                    install_thread.update_progress.connect(self._on_install_progress)  # 连接信号
                    install_thread.finished.connect(self._on_install_finished(response_json))  # 连接线程完成信号
                    install_thread.start()  # 启动线程

        except Exception as e:
            logger_manager.logger.error(f"在线安装插件时发生错误: {e}")
            QMessageBox.warning(self, "错误", "在线安装过程中发生错误")

    def _on_install_progress(self, progress):
        """处理安装进度更新"""
        self.progress_bar.setValue(progress)  # 更新进度条的值

    def _on_install_finished(self, plugin_info):
        """PIP 处理安装完成后的逻辑"""
        self.progress_bar.deleteLater()  # 清理进度条
        self._perform_updates([plugin_info], install_plugins=True)
        
        
    def uninstall_selected_plugins(self):
        """卸载选中的插件"""
        selected_rows = set(item.row() for item in self.table.selectedItems())
        plugins = self.plugin_manager.get_plugin_info_list()
        
        if not selected_rows:
            QMessageBox.information(self, "提示", "没有选中需要卸载的插件")
            return

        reply = QMessageBox.question(self, '确认卸载', 
                                   f'确定要卸载选中的 {len(selected_rows)} 个插件吗？',
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            for row in selected_rows:
                plugin_info = plugins[row]
                self._perform_uninstall(plugin_info)  # 执行卸载逻辑

    def _perform_uninstall(self, plugin_info):
        """执行卸载操作"""
        # 这里可以添加卸载插件的逻辑
        # logger_manager.logger.info(f"卸载插件: {plugin_info.get('name', '未知插件')}")
        # self.plugin_manager.uninstall_plugin(plugin_info)
        name = plugin_info.get('name', '未知插件')
        plugin_path = Path(PLUGIN_DIR) / name
        if plugin_path.exists():
            shutil.rmtree(plugin_path)
            logger_manager.logger.info(f"卸载插件: {name}")
        else:
            logger_manager.logger.warning(f"插件不存在: {name}")
            
    def _restart_app(self):
        """重启应用程序"""
        app_path = sys.executable
        if app_path.endswith('python.exe'):
            print("开发环境 请手动重启")
        else:
            pass
            # 暂时没有好的方法重启程序
            # 旧进程没有退出
            # 新进程启动后无法替换文件

        QApplication.quit()