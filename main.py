import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileSystemModel, QTreeView, QVBoxLayout, QWidget, QSplitter
from PyQt5.QtCore import Qt


class FileManager(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQt File Manager")
        self.setGeometry(100, 100, 1200, 800)

        self.main_layout = QVBoxLayout()

        self.splitter = QSplitter(Qt.Horizontal)

        self.model_left = QFileSystemModel()
        self.model_left.setRootPath('')

        self.model_right = QFileSystemModel()
        self.model_right.setRootPath('')

        self.tree_left = QTreeView()
        self.tree_left.setModel(self.model_left)
        self.tree_left.setRootIndex(self.model_left.index(''))
        self.tree_left.setColumnWidth(0, 250)

        self.tree_right = QTreeView()
        self.tree_right.setModel(self.model_right)
        self.tree_right.setRootIndex(self.model_right.index(''))
        self.tree_right.setColumnWidth(0, 250)

        self.splitter.addWidget(self.tree_left)
        self.splitter.addWidget(self.tree_right)

        self.container = QWidget()
        self.main_layout.addWidget(self.splitter)
        self.container.setLayout(self.main_layout)

        self.setCentralWidget(self.container)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FileManager()
    window.show()
    sys.exit(app.exec_())
