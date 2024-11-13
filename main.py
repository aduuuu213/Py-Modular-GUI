import os
import sys

from gui.main_window import MainWindow
from PySide2.QtWidgets import QApplication

from utils.config import ConfigManager
from utils.install import install_plugin_update

os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(os.path.dirname(__file__), 'Lib', 'site-packages', 'PySide2', 'plugins')

def main():
    app = QApplication(sys.argv)
    config_manager = ConfigManager()
    window = MainWindow(config_manager)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        msg = install_plugin_update()
        if msg:
            os.MessageBox(msg, "更新结果")
    except BaseException as e:
        pass
    main()
