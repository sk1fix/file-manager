import sys
import os
import string
import shutil
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileSystemModel, QTreeView, QVBoxLayout, QWidget, QSplitter, QComboBox, QHBoxLayout, QMenu, QAction, QMessageBox, QInputDialog
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl


class FileManager(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQt File Manager")
        self.setGeometry(150, 150, 1600, 800)

        self.main_layout = QVBoxLayout()

        self.splitter = QSplitter(Qt.Horizontal)

        self.model_left = QFileSystemModel()
        self.model_left.setRootPath('')

        self.model_right = QFileSystemModel()
        self.model_right.setRootPath('')

        # Создание левого дерева
        self.tree_left = CustomTreeView()
        self.tree_left.setModel(self.model_left)
        self.tree_left.setRootIndex(self.model_left.index(''))
        self.tree_left.setColumnWidth(0, 250)
        self.tree_left.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_left.customContextMenuRequested.connect(lambda pos: self.show_context_menu(pos, self.tree_left))
        self.tree_left.doubleClicked.connect(self.open_item)
        self.tree_left.setSortingEnabled(True)

        # Настройки Drag-and-Drop для левого дерева
        self.tree_left.setDragEnabled(True)
        self.tree_left.setAcceptDrops(True)
        self.tree_left.setDropIndicatorShown(True)

        # Создание правого дерева
        self.tree_right = CustomTreeView()
        self.tree_right.setModel(self.model_right)
        self.tree_right.setRootIndex(self.model_right.index(''))
        self.tree_right.setColumnWidth(0, 250)
        self.tree_right.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_right.customContextMenuRequested.connect(lambda pos: self.show_context_menu(pos, self.tree_right))
        self.tree_right.doubleClicked.connect(self.open_item)
        self.tree_right.setSortingEnabled(True)

        # Настройки Drag-and-Drop для правого дерева
        self.tree_right.setDragEnabled(True)
        self.tree_right.setAcceptDrops(True)
        self.tree_right.setDropIndicatorShown(True)

        # Добавление деревьев в интерфейс
        self.splitter.addWidget(self.tree_left)
        self.splitter.addWidget(self.tree_right)

        self.combo_left = QComboBox()
        self.combo_right = QComboBox()

        self.combo_left.setFixedHeight(40)
        self.combo_right.setFixedHeight(40)

        self.populate_combo_boxes()

        self.combo_left.currentIndexChanged.connect(
            lambda: self.change_root(self.combo_left, self.tree_left, self.model_left))
        self.combo_right.currentIndexChanged.connect(lambda: self.change_root(
            self.combo_right, self.tree_right, self.model_right))

        self.combo_layout = QHBoxLayout()
        self.combo_layout.addWidget(self.combo_left)
        self.combo_layout.addWidget(self.combo_right)

        self.container = QWidget()
        self.main_layout.addWidget(self.splitter)
        self.main_layout.addLayout(self.combo_layout)
        self.container.setLayout(self.main_layout)

        self.setCentralWidget(self.container)

        self.clipboard = None

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

    def show_context_menu(self, position, tree_view):
        """Show context menu with file operations."""
        index = tree_view.indexAt(position)
        if not index.isValid():
            return

        file_path = tree_view.model().filePath(index)

        menu = QMenu()

        copy_action = QAction("Копировать", self)
        copy_action.triggered.connect(lambda: self.copy_item(file_path))
        menu.addAction(copy_action)

        paste_action = QAction("Вставить", self)
        paste_action.setEnabled(self.clipboard is not None)
        paste_action.triggered.connect(lambda: self.paste_item(tree_view))
        menu.addAction(paste_action)

        rename_action = QAction("Переименовать", self)
        rename_action.triggered.connect(lambda: self.rename_item(file_path))
        menu.addAction(rename_action)

        delete_action = QAction("Удалить", self)
        delete_action.triggered.connect(lambda: self.delete_item(file_path))
        menu.addAction(delete_action)

        properties_action = QAction("Свойства", self)
        properties_action.triggered.connect(
            lambda: self.show_properties(file_path))
        menu.addAction(properties_action)

        menu.exec_(tree_view.viewport().mapToGlobal(position))

    def copy_item(self, file_path):
        """Copy the selected file or folder."""
        self.clipboard = file_path
        QMessageBox.information(
            self, "Копировать", f"Скопировано: {file_path}")

    def paste_item(self, tree_view):
        """Paste the copied item."""
        if self.clipboard:
            destination_index = tree_view.currentIndex()
            destination_path = tree_view.model().filePath(destination_index)
            if os.path.isdir(destination_path):
                try:
                    if os.path.isdir(self.clipboard):
                        shutil.copytree(self.clipboard, os.path.join(
                            destination_path, os.path.basename(self.clipboard)))
                    else:
                        shutil.copy(self.clipboard, destination_path)
                    QMessageBox.information(
                        self, "Вставить", f"Вставлено в: {destination_path}")
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Ошибка вставки: {e}")

    def rename_item(self, file_path):
        """Rename the selected file or folder."""
        file_name, file_extension = os.path.splitext(file_path)
        base_name = os.path.basename(file_name)
        new_name, ok = QInputDialog.getText(
            self, "Переименовать", "Введите новое имя:", text=base_name)
        if ok and new_name:
            try:
                new_path = os.path.join(os.path.dirname(
                    file_path), new_name + file_extension)
                os.rename(file_path, new_path)
                QMessageBox.information(
                    self, "Переименовать", f"Переименовано: {file_path} -> {new_path}")
            except Exception as e:
                QMessageBox.warning(
                    self, "Ошибка", f"Ошибка переименования: {e}")

    def delete_item(self, file_path):
        """Delete the selected file or folder."""
        reply = QMessageBox.question(
            self, "Удалить", f"Вы уверены, что хотите удалить {file_path}?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                QMessageBox.information(
                    self, "Удалить", f"Удалено: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Ошибка удаления: {e}")

    def show_properties(self, file_path):
        """Show properties of the selected file or folder."""
        try:
            if sys.platform == "win32":
                import ctypes
                from ctypes import wintypes

                class SHELLEXECUTEINFO(ctypes.Structure):
                    _fields_ = [
                        ("cbSize", ctypes.c_ulong),
                        ("fMask", ctypes.c_ulong),
                        ("hwnd", wintypes.HWND),
                        ("lpVerb", wintypes.LPCWSTR),
                        ("lpFile", wintypes.LPCWSTR),
                        ("lpParameters", wintypes.LPCWSTR),
                        ("lpDirectory", wintypes.LPCWSTR),
                        ("nShow", ctypes.c_int),
                        ("hInstApp", wintypes.HINSTANCE),
                        ("lpIDList", ctypes.c_void_p),
                        ("lpClass", wintypes.LPCWSTR),
                        ("hkeyClass", wintypes.HKEY),
                        ("dwHotKey", ctypes.c_ulong),
                        ("hIcon", wintypes.HANDLE),
                        ("hProcess", wintypes.HANDLE),
                    ]

                SEE_MASK_INVOKEIDLIST = 0x0000000C
                SW_SHOW = 5

                sei = SHELLEXECUTEINFO()
                sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
                sei.fMask = SEE_MASK_INVOKEIDLIST
                sei.hwnd = None
                sei.lpVerb = "properties"
                sei.lpFile = file_path
                sei.lpParameters = None
                sei.lpDirectory = None
                sei.nShow = SW_SHOW
                sei.hInstApp = None

                result = ctypes.windll.shell32.ShellExecuteExW(
                    ctypes.byref(sei))

                if not result:
                    raise ctypes.WinError()
            else:
                QMessageBox.information(self, "Свойства", f"Путь: {file_path}")
        except Exception as e:
            QMessageBox.warning(
                self, "Ошибка", f"Не удалось открыть свойства: {e}")

    def open_item(self, index):
        """Open the selected file or folder."""
        file_path = self.sender().model().filePath(index)
        if os.path.isdir(file_path):
            QMessageBox.information(
                self, "Открыть", f"Открыта папка: {file_path}")
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))


class CustomTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

        # Включаем сортировку
        self.setSortingEnabled(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            source_path = event.mimeData().urls()[0].toLocalFile()

            # Определяем папку назначения
            index = self.indexAt(event.pos())
            if not index.isValid():
                destination_path = self.model().rootPath()
            else:
                destination_path = self.model().filePath(index)
                if not os.path.isdir(destination_path):
                    QMessageBox.warning(self, "Ошибка", "Перемещать файлы можно только в папки.")
                    return

            # Перенос файла
            try:
                new_path = os.path.join(destination_path, os.path.basename(source_path))
                shutil.move(source_path, new_path)
                QMessageBox.information(self, "Успех", f"Файл {source_path} перемещён в {new_path}")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Ошибка перемещения: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FileManager()
    window.show()
    sys.exit(app.exec_())
