import sys
import os
import string
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileSystemModel, QTreeView, QVBoxLayout, QWidget, QSplitter, QComboBox, QHBoxLayout
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

        self.combo_left = QComboBox()
        self.combo_right = QComboBox()

        self.populate_combo_boxes()

        self.combo_left.currentIndexChanged.connect(lambda: self.change_root(self.combo_left, self.tree_left, self.model_left))
        self.combo_right.currentIndexChanged.connect(lambda: self.change_root(self.combo_right, self.tree_right, self.model_right))

        self.combo_layout = QHBoxLayout()
        self.combo_layout.addWidget(self.combo_left)
        self.combo_layout.addWidget(self.combo_right)

        self.container = QWidget()
        self.main_layout.addWidget(self.splitter)
        self.main_layout.addLayout(self.combo_layout)
        self.container.setLayout(self.main_layout)

        self.setCentralWidget(self.container)

    def populate_combo_boxes(self):
        """Populate combo boxes with available drives and Desktop."""
        drives = self.get_available_drives()
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if os.path.exists(desktop):
            drives.append("Рабочий стол")
        self.combo_left.addItems(drives)
        self.combo_right.addItems(drives)

    def get_available_drives(self):
        """Return a list of available drives on the system."""
        if sys.platform == "win32":
            return [f"{drive}:\\" for drive in string.ascii_uppercase if os.path.exists(f"{drive}:\\")]
        else:
            return ["/"]

    def change_root(self, combo_box, tree_view, model):
        """Change the root directory of the tree view based on combo box selection."""
        selected_path = combo_box.currentText()
        if selected_path == "Рабочий стол":
            selected_path = os.path.join(os.path.expanduser("~"), "Desktop")
        model.setRootPath(selected_path)
        tree_view.setRootIndex(model.index(selected_path))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FileManager()
    window.show()
    sys.exit(app.exec_())
