import configparser
import os
from datetime import datetime

class ConfigManager:
    def __init__(self, config_file='utils/config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        
        if not os.path.exists(self.config_file):
            self.create_default_config()
        else:
            self.config.read(self.config_file, encoding='utf-8')

    def load_all(self) -> dict:
        """加载所有配置到扁平字典"""
        result = {}
        
        # 处理所有 sections
        for section in self.config.sections():
            for key, value in self.config.items(section):
                if section == 'window_ui':
                    # window_ui section 中的键直接使用
                    result[key] = self._parse_value(value)
                else:
                    # 其他 section 的键加上 section 前缀
                    full_key = f"{section}.{key}"
                    result[full_key] = self._parse_value(value)
                
        return result

    def save_all(self, data: dict):
        """保存扁平字典到配置文件"""
        # 确保必要的section存在
        if 'window_ui' not in self.config:
            self.config.add_section('window_ui')
        
        # 整理数据到sections
        for full_key, value in data.items():
            if '.' in full_key:
                section, key = full_key.split('.', 1)
                if section not in self.config:
                    self.config.add_section(section)
                self.config.set(section, key, str(value))
            else:
                # 没有点号的键放入window_ui
                self.config.set('window_ui', full_key, str(value))
        
        # 保存到文件
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def _parse_value(self, value: str):
        """智能解析配置值的类型"""
        # 布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 整数
        try:
            return int(value)
        except ValueError:
            pass
            
        # 浮点数
        try:
            return float(value)
        except ValueError:
            pass
            
        # 列表 (格式如: "[1, 2, 3]")
        if value.startswith('[') and value.endswith(']'):
            try:
                return eval(value)  # 警告：在生产环境中要小心使用eval
            except:
                pass
                
        # 默认返回字符串
        return value

    def create_default_config(self):
        """创建默认配置文件"""
        self.config['DEFAULT'] = {
            'version': '1.0',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.config['window'] = {
            'width': 1400,
            'height': 800,
            'title': "应用程序"
        }
        self.config['window_ui'] = {}
        self.save()

    def get(self, section, key, fallback=None):
        return self.config.get(section, key, fallback=fallback)

    def set(self, section, key, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))

    def save(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def get_flask_port(self):
        return self.config.getint('Flask', 'port', fallback=5000)