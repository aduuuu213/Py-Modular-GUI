from PySide2.QtWidgets import QMessageBox

def show_message(self, title, message):
    QMessageBox.information(self, title, message)