# 安装插件更新包
import json
import traceback
from pathlib import Path

from constants.config import PLUGIN_DIR, PLUGIN_UPDATE_CACHE_DIR


def _apply_pending_updates(plugin_name, file_path):
    """应用待更新的插件"""
    root_dir = Path(__file__).resolve().parent.parent
    plugin_dir = root_dir / PLUGIN_DIR
    try:
        import zipfile
        with zipfile.ZipFile(file_path) as zf:
            # 检查压缩包内文件名是否包含中文
            file_list = zf.namelist()
            if any('\u4e00' <= char <= '\u9fff' for fname in file_list for char in fname):
                raise Exception("压缩包内文件名不能包含中文字符")
                
            # 情况1: 包含pyd文件
            if any(f.endswith('.pyd') for f in file_list):
                print('pyd 插件')
                for f in file_list:
                    if f.endswith('.pyd'):
                        print(plugin_dir)
                        zf.extract(f, plugin_dir)
                return True
                
            # 情况2: 第一层有__init__.py
            if '__init__.py' in file_list:
                print('__init__ 插件')
                target_dir = plugin_dir / plugin_name
                zf.extractall(target_dir)
                return True
                    
            # 情况3: 第一层是文件夹
            first_item = file_list[0]
            if '/' in first_item:  # 是文件夹
                print("目录插件")
                zf.extractall(plugin_dir)
                return True
        return False
    except Exception as e:
        traceback.print_exc()
        return False

def install_plugin_update():
    """安装插件更新包"""
    retstr = ""
    json_file_path = Path(f'{PLUGIN_UPDATE_CACHE_DIR}/update_info.json')
    if  json_file_path.exists():
        with open(json_file_path, 'r') as f:
            update_info = json.load(f)
        for plugin_name, file_path in update_info.items():
            print(f"插件名: {plugin_name}, 文件路径: {file_path}")
            status = _apply_pending_updates(plugin_name, file_path)
            if status:
                retstr += f"插件 {plugin_name} 更新成功\n"
            else:
                retstr += f"插件 {plugin_name} 更新失败\n"
    with open(json_file_path, 'w') as f:
        json.dump({}, f)
    return retstr

