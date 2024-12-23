import sys
import os
import string
import shutil
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow,
    QFileSystemModel, QTreeView,
    QVBoxLayout, QWidget,
    QSplitter, QComboBox,
    QHBoxLayout, QMenu,
    QAction, QMessageBox,
    QInputDialog
)
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl


class FileManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt File Manager")
        self.setGeometry(150, 150, 1600, 800)
        self.action_stack = []  # Стек для действий (Ctrl+Z)
        self.main_layout = QVBoxLayout()

        self.splitter = QSplitter(Qt.Horizontal)

        # Модели файловой системы
        self.model_left = QFileSystemModel()
        self.model_left.setRootPath('')

        self.model_right = QFileSystemModel()
        self.model_right.setRootPath('')

        # Создание левого дерева
        self.tree_left = CustomTreeView(self)  # Передаём ссылку на FileManager
        self.tree_left.setModel(self.model_left)
        self.tree_left.setRootIndex(self.model_left.index(''))
        self.tree_left.setColumnWidth(0, 250)
        self.tree_left.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_left.customContextMenuRequested.connect(
            lambda pos: self.show_context_menu(pos, self.tree_left))
        self.tree_left.doubleClicked.connect(self.open_item)
        self.tree_left.setSortingEnabled(True)

        # Настройки Drag-and-Drop для левого дерева
        self.tree_left.setDragEnabled(True)
        self.tree_left.setAcceptDrops(True)
        self.tree_left.setDropIndicatorShown(True)

        # Создание правого дерева
        self.tree_right = CustomTreeView(self)  # Передаём ссылку на FileManager
        self.tree_right.setModel(self.model_right)
        self.tree_right.setRootIndex(self.model_right.index(''))
        self.tree_right.setColumnWidth(0, 250)
        self.tree_right.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_right.customContextMenuRequested.connect(
            lambda pos: self.show_context_menu(pos, self.tree_right))
        self.tree_right.doubleClicked.connect(self.open_item)
        self.tree_right.setSortingEnabled(True)

        # Настройки Drag-and-Drop для правого дерева
        self.tree_right.setDragEnabled(True)
        self.tree_right.setAcceptDrops(True)
        self.tree_right.setDropIndicatorShown(True)
        # Добавление деревьев в интерфейс
        self.splitter.addWidget(self.tree_left)
        self.splitter.addWidget(self.tree_right)

        # Создание выпадающих списков для выбора корневого каталога
        self.combo_left = QComboBox()
        self.combo_right = QComboBox()

        self.combo_left.setFixedHeight(40)
        self.combo_right.setFixedHeight(40)

        # Заполнение выпадающих списков доступными дисками
        self.populate_combo_boxes()

        # Изменение корня дерева при изменении выбора в выпадающем списке
        self.combo_left.currentIndexChanged.connect(
            lambda: self.change_root(self.combo_left, self.tree_left, self.model_left))
        self.combo_right.currentIndexChanged.connect(lambda: self.change_root(
            self.combo_right, self.tree_right, self.model_right))

        # Компоновка выпадающих списков
        self.combo_layout = QHBoxLayout()
        self.combo_layout.addWidget(self.combo_left)
        self.combo_layout.addWidget(self.combo_right)

        # Основная компоновка
        self.container = QWidget()
        self.main_layout.addWidget(self.splitter)
        self.main_layout.addLayout(self.combo_layout)
        self.container.setLayout(self.main_layout)

        self.setCentralWidget(self.container)

        self.clipboard = None  # Буфер обмена для копирования и вставки

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

        new_folder_action = QAction("Создать папку", self)
        new_folder_action.triggered.connect(
            lambda: self.create_new_folder(file_path))
        menu.addAction(new_folder_action)

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
                    new_path = os.path.join(destination_path, os.path.basename(self.clipboard))
                    if os.path.isdir(self.clipboard):
                        shutil.copytree(self.clipboard, new_path)
                    else:
                        shutil.copy(self.clipboard, new_path)
                    # Запись действия вставки
                    self.record_action("paste", source=self.clipboard, destination=new_path)
                    QMessageBox.information(self, "Вставить", f"Вставлено в: {destination_path}")
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
                new_path = os.path.join(os.path.dirname(file_path), new_name + file_extension)
                os.rename(file_path, new_path)
                # Запись действия переименования
                self.record_action("rename", old_path=file_path, new_path=new_path)
                QMessageBox.information(self, "Переименовать", f"Переименовано: {file_path} -> {new_path}")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Ошибка переименования: {e}")

    def delete_item(self, file_path):
        """Delete the selected file or folder."""
        reply = QMessageBox.question(
            self, "Удалить", f"Вы уверены, что хотите удалить {file_path}?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                is_dir = os.path.isdir(file_path)
                backup_path = shutil.copytree(file_path, file_path + "_backup") if is_dir else shutil.copy(file_path, file_path + "_backup")
                if is_dir:
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                # Запись действия удаления
                self.record_action("delete", original_path=file_path, backup_path=backup_path, is_dir=is_dir)
                QMessageBox.information(self, "Удалить", f"Удалено: {file_path}")
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

    def create_new_folder(self, parent_path):
        if not os.path.isdir(parent_path):
            QMessageBox.warning(self, "Ошибка", "Нельзя создать папку в файле.")
            return

        new_folder_name, ok = QInputDialog.getText(self, "Создать папку", "Введите имя папки:")
        if ok and new_folder_name:
            new_folder_path = os.path.join(parent_path, new_folder_name)
            try:
                os.makedirs(new_folder_path)
                # Запись действия создания папки
                self.record_action("create_folder", folder_path=new_folder_path)
                QMessageBox.information(self, "Успех", f"Папка '{new_folder_name}' создана.")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось создать папку: {e}")

    def open_item(self, index):
        """Open the selected file or folder."""
        file_path = self.sender().model().filePath(index)
        if os.path.isdir(file_path):
            QMessageBox.information(
                self, "Открыть", f"Открыта папка: {file_path}")
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        
    def keyPressEvent(self, event):
        """Handle key press events."""
        tree_view = self.tree_left if self.tree_left.hasFocus() else self.tree_right
        index = tree_view.currentIndex()
        if not index.isValid():
            return

        file_path = tree_view.model().filePath(index)

        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C:
            # Копирование
            self.copy_item(file_path)
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_V:
            # Вставка
            self.paste_item(tree_view)
        elif event.key() == Qt.Key_Delete:
            # Удаление
            self.delete_item(file_path)
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Z:
            # Отмена действия
            self.undo_last_action()
                
    def record_action(self, action_type, **kwargs):
        """Записывает действие в стек."""
        self.action_stack.append({'type': action_type, 'data': kwargs})

    def undo_last_action(self):
        """Отменяет последнее действие."""
        if not self.action_stack:
            QMessageBox.information(self, "Отмена", "Нет действий для отмены.")
            return

        last_action = self.action_stack.pop()
        action_type = last_action['type']
        data = last_action['data']

        try:
            if action_type == "delete":
                # Восстановление удалённого элемента
                if data['is_dir']:
                    shutil.copytree(data['backup_path'], data['original_path'])
                else:
                    shutil.copy(data['backup_path'], data['original_path'])
                QMessageBox.information(self, "Отмена", "Удаление отменено.")
            elif action_type == "rename":
                # Отмена переименования
                os.rename(data['new_path'], data['old_path'])
                QMessageBox.information(self, "Отмена", "Переименование отменено.")
            elif action_type == "paste":
                # Удаление вставленного элемента
                if os.path.isdir(data['destination']):
                    shutil.rmtree(data['destination'])
                else:
                    os.remove(data['destination'])
                QMessageBox.information(self, "Отмена", "Вставка отменена.")
            elif action_type == "create_folder":
                # Удаление созданной папки
                if os.path.exists(data['folder_path']):
                    shutil.rmtree(data['folder_path'])
                    QMessageBox.information(self, "Отмена", "Создание папки отменено.")
            elif action_type == "move":
                # Перемещение обратно в исходное место
                if os.path.exists(data['destination']):
                    shutil.move(data['destination'], data['source'])
                    QMessageBox.information(self, "Отмена", f"Перемещение отменено. {data['destination']} возвращён в {data['source']}.")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при отмене действия: {e}")


class CustomTreeView(QTreeView):
    def __init__(self, file_manager, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.file_manager = file_manager  # Устанавливаем ссылку на FileManager
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

            try:
                new_path = os.path.join(destination_path, os.path.basename(source_path))
                shutil.move(source_path, new_path)
                # Запись действия перемещения
                self.file_manager.record_action("move", source=source_path, destination=new_path)
                QMessageBox.information(self, "Успех", f"Файл {source_path} перемещён в {new_path}")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Ошибка перемещения: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FileManager()
    window.show()
    sys.exit(app.exec_())
