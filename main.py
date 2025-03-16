import sys

from PyQt5.QtWidgets import QApplication

from file_manager import FileManager


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FileManager()
    window.show()
    sys.exit(app.exec_())

