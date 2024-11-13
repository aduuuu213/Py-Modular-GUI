PLUGIN_INFO = {
    'name': '演示插件',  # 插件别名
    'version': '1.1',    # 可选：版本号
    'description': '这是一个示例插件，旨在展示插件的基本功能和结构。',  # 可选：描述
    'update_url': ''  # 可选：更新地址
}

from .window import demo

# 插件导入 QWidget 对象的类
# 保证插件类名和文件名一致
__all__ = ['demo']

# update_url 应该返回如下信息 json 格式
# {
#     "name": "插件名称",
#     "version": "1.1",
#     "description": "插件描述，提供详细的功能介绍和使用指南。",
#     "download_url": "https://example.com/plugins/demo/download/1.1",
#     "release_notes": "更新说明，包含新特性和修复的bug。",
#     "min_app_version": "1.0",
#     "dependencies": {
#         "some-lib": ">=1.0"
#     }
# }
# download_url 下载为更新zip的压缩包
# 完成后，程序自动重启后，解压进行替换更新