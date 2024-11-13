import requests
from utils.logger_manager import logger_manager


def download_file(url, file_path):
    response = requests.get(url)
    with open(file_path, 'wb') as file:
        file.write(response.content)


def get_json(url, **kwargs):
    try:
        if len(url) == 0:
            return {}
        response = requests.get(url, **kwargs)
        if response.status_code == 200:
            return response.json()
        else:
            logger_manager.logger.error(f"获取JSON数据时发生错误: {response.status_code}")
            return {}
    except Exception as e:
        logger_manager.logger.error(f"获取JSON数据时发生错误: {e}")
        return {}
