PLUGIN_INFO = {
    'name': '马士基',  # 插件别名
    'version': '1.2',    # 可选：版本号
    'description': '马士基订舱插件',  # 可选：描述
    'update_url': 'http://package.smalldu.cn/package/msk/info.json'  # 可选：更新地址
}

from .son_window import msk

__all__ = ['msk']