import os
import subprocess
import shutil
from setuptools import setup

def compile_plugin(dir_name, plugin_dir):
    plugin_path = os.path.join(dir_name, plugin_dir)
    init_file = os.path.join(plugin_path)
    cmd = [
        'python', '-m', 'nuitka',
        '--module',
        init_file,
        '--output-dir=build'
    ]
    print(cmd)
    subprocess.run(cmd, check=True)

    # 新建app文件夹
    app_dir = os.path.join('build', 'app', dir_name)
    os.makedirs(app_dir, exist_ok=True)

    # 移动并重命名生成的.pyd文件
    pyd_file = os.path.join('build', f'{plugin_dir[:-3]}.cp38-win32.pyd')  # 删除.py后缀
    print(pyd_file)
    if os.path.exists(pyd_file):
        # 去掉文件名中的 'cp38-win32' 部分
        base_name = plugin_dir[:-3]  # 删除.py后缀
        target_file_name = f'{base_name}.pyd'  # 目标文件名
        target_dir = os.path.join(app_dir, target_file_name)  # 创建对应的文件夹
        shutil.move(pyd_file, target_dir)

# 编译插件
for plugin_dir in os.listdir('gui'):
    print(plugin_dir)
    if plugin_dir.endswith('.py') and plugin_dir != '__init__.py':
        compile_plugin('gui', plugin_dir)
        



# setup()


# python -m nuitka --module 

# nuitka --module msk --include-package=msk