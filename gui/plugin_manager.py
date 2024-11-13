import importlib
import importlib.util
import os
import sys
import traceback

from PySide2.QtWidgets import QVBoxLayout, QWidget


class PluginManager:
    def __init__(self, plugins_folder = 'plugins'):
        self.plugins_folder = plugins_folder
        self.plugins = {}

    def load_plugins(self):
        # 加载 plugins 包中的所有插件
        self._load_plugins_from_package()

    def _load_plugins_from_package(self):
        # 导入 plugins 包
        package_name = self.plugins_folder
        package = importlib.import_module(package_name)
        package_path = os.path.dirname(package.__file__)
        # 加载 .pyd 文件
        for file in os.listdir(package_path):
            if file.endswith('.pyd'):
                try:
                    module_name = os.path.splitext(file)[0]
                    spec = importlib.util.spec_from_file_location(module_name, os.path.join(package_path, file))
                    print(f"目录: {package_path}")
                    print(f"目录插件: {module_name}")
                    print(spec)
                    if spec:
                        module = importlib.util.module_from_spec(spec)
                        try:
                            spec.loader.exec_module(module)
                            # 获取插件信息
                            plugin_info = getattr(module, 'PLUGIN_INFO', {})
                            print(f"插件信息: {plugin_info}")
                            plugin_alias = plugin_info.get('name', module_name)  # 如果没有设置别名，使用文件夹名
                            # 查找模块中的 QWidget 子类
                            for attr_name in dir(module):
                                attr = getattr(module, attr_name)
                                if isinstance(attr, type) and issubclass(attr, QWidget):
                                    setattr(attr, 'plugin_name', module_name)
                                    setattr(attr, 'plugin_alias', plugin_alias)
                                    setattr(attr, 'plugin_info', plugin_info)
                                    self.plugins[attr_name] = attr
                        except Exception as e:
                            print(f"加载插件 {module_name} 失败: {str(e)}")
                except Exception as e:
                    traceback.print_exc()
                    print(f"导入 {file} 失败: {str(e)}")
                    continue
        
        # 加载文件夹
        for item in os.listdir(package_path):
            folder_path = os.path.join(package_path, item)
            if os.path.isdir(folder_path):
                init_file = os.path.join(folder_path, '__init__.py')
                if os.path.exists(init_file):
                    try:
                        # 构造模块名
                        module_name = f'{package_name}.{item}'
                        # 导入模块
                        module = importlib.import_module(module_name)
                        # 获取插件信息
                        plugin_info = getattr(module, 'PLUGIN_INFO', {})
                        print(f"插件信息: {plugin_info}")
                        plugin_alias = plugin_info.get('name', item)  # 如果没有设置别名，使用文件夹名
                        # 查找模块中的 QWidget 子类
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if isinstance(attr, type) and issubclass(attr, QWidget):
                                setattr(attr, 'plugin_name', item)
                                setattr(attr, 'plugin_alias', plugin_alias)
                                setattr(attr, 'plugin_info', plugin_info)
                                self.plugins[attr_name] = attr
                    except Exception as e:
                        print(f"加载插件文件夹 {item} 失败: {str(e)}")
                        traceback.print_exc()

    def get_plugin_names(self):
        return list(self.plugins.keys())

    def get_plugin(self, name):
        # 返回插件类而不是实例
        return self.plugins.get(name)

    def get_plugin_alias(self, name):
        """获取插件别名
        Args:
            name: 插件类名
        Returns:
            str: 插件别名或原名
        """
        try:
            plugin_class = self.plugins.get(name)
            if not plugin_class:
                return name
            # 先尝试从类属性获取
            plugin_info = getattr(plugin_class, 'plugin_alias', None)
            return plugin_info
        except Exception as e:
            print(f"获取插件 {name} 别名失败: {str(e)}")
            return name
    
    def get_plugin_name_by_alias(self, alias):
        """根据别名获取插件名"""
        for plugin_name, plugin_class in self.plugins.items():
            if self.get_plugin_alias(plugin_name) == alias:
                return plugin_name
        return None

    def get_plugin_info_list(self):
        """获取所有插件信息列表"""
        plugin_info_list = []
        for plugin_name in self.get_plugin_names():
            module = self.plugins.get(plugin_name)
            if hasattr(module, 'plugin_info'):
                plugin_info_list.append(module.plugin_info)
        return plugin_info_list

def unload_all_plugins(self):
    """卸载所有插件"""
    for plugin_class in self.plugins[:]:  # 使用切片以避免修改列表时出错
        self.remove_plugin(plugin_class)

class PluginArea(QWidget):
    def __init__(self):
        super().__init__()
        self.plugin_layout = QVBoxLayout(self)
        self.plugins = []

    def add_plugin(self, plugin_class):
        # 创建插件实例并添加
        plugin = plugin_class()  # 这里创建实例
        self.plugins.append(plugin)
        self.plugin_layout.addWidget(plugin)

    def remove_plugin(self, plugin_class):
        plugins_to_remove = [p for p in self.plugins if p.__class__ == plugin_class]
        for plugin in plugins_to_remove:
            self.plugins.remove(plugin)
            self.plugin_layout.removeWidget(plugin)
            plugin.setParent(None)  # 确保完全断开父子关系
            plugin.deleteLater()