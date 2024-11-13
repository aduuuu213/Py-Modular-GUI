PLUGIN_INFO = {
    'name': '演示插件',  # 插件别名
    'version': '1.1',    # 可选：版本号
    'description': '这是一个示例插件',  # 可选：描述
    'update_url': ''  # 可选：更新地址
}

from .window import demo

__all__ = ['demo']

# 检查更新的网址返回json信息
# {
#     "name": "插件名称",
#     "version": "1.1",
#     "description": "插件描述",
#     "download_url": "https://example.com/plugins/demo/download/1.1",
#     "release_notes": "更新说明",
#     "min_app_version": "1.0",
#     "dependencies": {
#         "some-lib": ">=1.0"
#     }
# }