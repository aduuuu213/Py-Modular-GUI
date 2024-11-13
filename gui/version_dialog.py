import json
import os
import shutil
import tempfile
from pathlib import Path

import requests
from PySide2.QtCore import Qt
from PySide2.QtWidgets import (QApplication, QDialog, QHeaderView, QMessageBox,QProgressBar,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout)

from constants.config import PLUGIN_DIR, PLUGIN_UPDATE_CACHE_DIR
from constants.messages import *
from utils.logger_manager import logger_manager
from utils.requests import download_file, get_json


class VersionDialog(QDialog):
    def __init__(self, plugin_manager, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self.window = parent
        self.setWindowTitle("插件版本信息")
        self.resize(500, 400)
        
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
        
        layout.addWidget(self.table)
        layout.addWidget(self.check_button)
        layout.addWidget(self.update_button)
        
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
                if latest_version > current_version:    
                    self.table.setItem(row, 3, QTableWidgetItem(WARNING_MESSAGE_NEW_VERSION_AVAILABLE))
                else:
                    self.table.setItem(row, 3, QTableWidgetItem(WARNING_MESSAGE_ALREADY_LATEST_VERSION))
            except Exception as e:
                logger_manager.error(f"检查插件更新时发生错误: {e}")
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

    def _perform_updates(self, plugins_to_update):
        """执行更新操作"""
        root_dir = Path(__file__).resolve().parent.parent
        temp_dir = root_dir / PLUGIN_UPDATE_CACHE_DIR
        temp_dir.mkdir(exist_ok=True)
        print(f"临时目录: {temp_dir}")
        
        # 创建进度条
        progress_bar = QProgressBar(self)
        progress_bar.setRange(0, len(plugins_to_update))
        progress_bar.setValue(0)
        
        # 创建一个布局来放置进度条
        layout = QVBoxLayout()
        layout.addWidget(progress_bar)
        self.setLayout(layout)  # 假设在一个 QWidget 中

        json_write = {}
        for index, plugin in enumerate(plugins_to_update):
            try:
                # 获取更新信息
                update_info = get_json(plugin['update_url'], timeout=5)
                
                # 下载新版本
                download_url = update_info['download_url']
                plugin_name = update_info['plugin_name']
                print(f"插件名: {plugin_name}")
                # 下载到临时目录
                temp_file = temp_dir / f"{plugin_name}_{update_info['version']}.zip"
                print(f"下载文件: {temp_file}")
                download_file(download_url, temp_file)
                json_write[plugin_name] = str(temp_file)
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
                QApplication.quit()
                

    def _write_update_info(self, json_write):
        """写入更新信息到配置文件"""
        print(f"写入更新信息: {PLUGIN_UPDATE_CACHE_DIR}/update_info.json")
        with open(f'{PLUGIN_UPDATE_CACHE_DIR}/update_info.json', 'w') as f:
            json.dump(json_write, f)
