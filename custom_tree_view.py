import shutil
import os
from PyQt5.QtWidgets import QTreeView, QMessageBox


class CustomTreeView(QTreeView):
    def __init__(self, file_manager, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.file_manager = file_manager
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

        self.setSortingEnabled(True)

    def dragEnterEvent(self, event):
        """Handles the drag enter event. Allows dragging only if the data contains URLs."""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Handles the drag move event. Allows moving only if the data contains URLs."""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Handles the drop event. Moves the file or folder to the target directory."""
        if event.mimeData().hasUrls():
            source_path = event.mimeData().urls()[0].toLocalFile()
            index = self.indexAt(event.pos())
            if not index.isValid():
                destination_path = self.model().rootPath()
            else:
                destination_path = self.model().filePath(index)
                if not os.path.isdir(destination_path):
                    QMessageBox.warning(
                        self, "Ошибка", "Перемещать файлы можно только в папки.")
                    return

            try:
                new_path = os.path.join(
                    destination_path, os.path.basename(source_path))
                shutil.move(source_path, new_path)
                self.file_manager.record_action(
                    "move", source=source_path, destination=new_path)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Ошибка перемещения: {e}")
