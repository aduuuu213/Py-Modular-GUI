# 自动打包插件
# 上传到七牛云

import json
import subprocess
import traceback
import zipfile
from pathlib import Path

from qiniu import Auth, etag, put_file

from constants.config import PLUGIN_DIR
try:
    from develop.config import ACCESS_KEY, BASE_URL, BUCKET_NAME, SECRET_KEY
except:
    pass


class PluginPackager:
    def __init__(self, access_key: str, secret_key: str, bucket_name: str, base_url: str):
        self.auth = Auth(access_key, secret_key)
        self.bucket_name = bucket_name
        self.base_url = base_url

    def upload_file(self, file_path: Path, key: str, package_name: str, dir: str = "package") -> str:
        token = self.auth.upload_token(self.bucket_name, f"{dir}/{package_name}/{key}")
        ret, info = put_file(token, f"{dir}/{package_name}/{key}", str(file_path), version="v2")
        
        if info.status_code != 200:
            raise Exception(f"上传失败: {info.error}")
            
        return f"{dir}/{package_name}/{key}"

    def _increment_version(self, current_version: str) -> str:
        version_parts = list(map(int, current_version.split(".")))
        while len(version_parts) < 3:
            version_parts.append(0)
        major, minor, patch = version_parts
        patch += 1
        return f"{major}.{minor}.{patch}"
    
    def _load_or_create_info(self, info_path: Path, plugin_name: str) -> dict:
        """加载或创建插件信息文件"""
        if info_path.exists():
            try:
                with open(info_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                raise Exception(f"插件信息文件 {info_path} 格式错误")
        
        # 创建新的信息文件
        default_info = {
            "name": plugin_name,
            "version": "0.0.0",
            "description": "",
            "author": "",
            "release_notes": "",
            "download_url": ""
        }
        
        self._save_info(info_path, default_info)
        return default_info

    def _save_info(self, info_path: Path, info: dict):
        """保存插件信息到文件"""
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=4)

    def _build_plugin(self, plugin_path: Path) -> Path:
        cmd = [
            "python", "-m", "nuitka",
            "--module", str(plugin_path),
            "--output-dir=build",
            f"--include-package={plugin_path.stem}"
        ]
        print(f"打包命令: {cmd}")
        try:
            subprocess.run(cmd, check=True)
            # 判断是否打包成功
            if ".py" in plugin_path.stem:
                plugin_name = plugin_path.stem[:-3]
            else:
                plugin_name = plugin_path.stem
            package_dir = Path(f"build/{plugin_name}.cp38-win32.pyd")
            print("打包插件路径: ", package_dir)
            if not package_dir.exists():
                raise Exception("插件 打包失败")
            # 重命名
            new_package_dir = package_dir.with_name(f"{plugin_name}.pyd")
            if new_package_dir.exists():  # 检查目标文件是否存在
                new_package_dir.unlink()  # 删除已存在的文件
            package_dir.rename(new_package_dir)
            print("重命名插件路径： ", new_package_dir)
            # 使用zip压缩
            zip_file = new_package_dir.with_suffix(".zip")
            with zipfile.ZipFile(zip_file, "w") as zipf:
                zipf.write(new_package_dir, arcname=new_package_dir.name)
            print("更新包路径：", zip_file)
            return zip_file
        except subprocess.CalledProcessError as e:
            raise Exception(f"打包失败: {e.stderr.decode()}")

    def package_and_upload(self, plugin_name: str, release_notes: str):
        plugin_dir = Path(PLUGIN_DIR) / plugin_name
        info_path = plugin_dir / "info.json"
        init_path = plugin_dir / "__init__.py"

        # 读取或创建插件信息
        try:
            info = self._load_or_create_info(info_path, plugin_name)
        except Exception as e:
            print(f"错误: {e}")
            return
        print(info)
        # 更新版本
        old_version = info["version"]
        new_version = self._increment_version(old_version)
        print(f"旧版本: {old_version}")
        print(f"新版本: {new_version}")
        # 更新 __init__.py 中的版本号
        self._update_init_version(init_path, old_version, new_version)
        
        # 打包上传
        try:
            package_path = self._build_plugin(plugin_dir)
            download_url = f"{self.base_url}/{self.upload_file(package_path, f'{plugin_name}_{new_version}.zip', plugin_name)}"
            
            # 更新并上传信息文件
            info.update({
                "version": new_version,
                "release_notes": release_notes,
                "download_url": download_url
            })
            
            self._save_info(info_path, info)
            self.upload_file(info_path, "info.json", plugin_name)
            
            print(f"插件 {plugin_name} v{new_version} 更新成功")
            
        except Exception as e:
            traceback.print_exc()
            print(f"更新失败: {e}")

    def _update_init_version(self, init_path: Path, old_version: str, new_version: str):
        """更新 __init__.py 中的版本号"""
        if not init_path.exists():
            raise Exception(f"找不到 {init_path}")
        
        try:
            # 读取文件内容
            content = init_path.read_text(encoding='utf-8')
            
            # 替换版本号
            version_pattern = f"'version': '{old_version}'"
            new_version_str = f"'version': '{new_version}'"
            
            if version_pattern not in content:
                # 如果没找到版本号，就在文件开头添加
                raise Exception(f"找不到版本号 {version_pattern}")
            else:
                # 替换已存在的版本号
                content = content.replace(version_pattern, new_version_str)
            
            # 写回文件
            init_path.write_text(content, encoding='utf-8')
            
        except Exception as e:
            raise Exception(f"更新版本号失败: {str(e)}")



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("package_name", help="插件名")
    parser.add_argument("release_notes", help="更新说明")
    args = parser.parse_args()

    packager = PluginPackager(
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        bucket_name=BUCKET_NAME,
        base_url=BASE_URL
    )
    
    packager.package_and_upload(args.package_name, args.release_notes)