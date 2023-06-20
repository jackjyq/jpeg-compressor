import multiprocessing
import shutil
import sys
import time
from multiprocessing import Process, Queue
from pathlib import Path
from queue import Empty
from typing import Callable

from PIL import Image
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtGui import (
    QDragEnterEvent,
    QDropEvent,
    QIcon,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QStatusBar,
    QWidget,
)

import compressor


class DirLineEdit(QLineEdit):
    def __init__(self, parent=None):
        """A QLineEdit that accepts drag and drop of directory path"""
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_dir():
                self.setText(str(path.resolve()))
                break


class StartThread(QThread):
    progress = pyqtSignal(int)

    def __init__(
        self,
        *,
        num_processes: int,
        counter,
        tasks: Queue,
        max_width: int,
    ) -> None:
        super().__init__()
        self.num_processes = num_processes
        self.counter = counter
        self.tasks = tasks
        self.max_width = max_width

    def run(self):
        # start multi-processes
        processes = []
        for _ in range(self.num_processes):
            p = multiprocessing.Process(
                target=compressor.compress_and_save_many,
                kwargs={
                    "counter": self.counter,
                    "tasks": self.tasks,
                    "max_width": self.max_width,
                },
            )
            processes.append(p)
            p.start()
        while self.counter.value > 0:
            self.progress.emit(self.counter.value)
            time.sleep(0.1)
        # wait to finish
        for p in processes:
            p.join()


class StopThread(QThread):
    def run(self) -> None:
        return


class MainWindow(QWidget):
    def __init__(self):
        """main window of the app

        Refs:
            https://doc.qt.io/qtforpython-6/
        """
        super().__init__()
        # used to store the tasks
        self.tasks = multiprocessing.Queue()
        self.counter = multiprocessing.Value("i", 0)

        self.input_dir_label = QLabel("输入文件夹: ")
        self.input_dir_line_edit = self.get_dir_line_edit(
            Path.home().joinpath("Desktop")
        )
        self.input_dir_browse_btn = self.get_browse_dir_btn(self.input_dir_line_edit)

        self.output_dir_label = QLabel("输出文件夹: ")
        self.output_dir_line_edit = self.get_dir_line_edit(
            Path.home().joinpath("Desktop")
        )
        self.output_dir_browse_btn = self.get_browse_dir_btn(self.output_dir_line_edit)

        self.include_subdir_label = QLabel("包含子文件夹: ")
        self.include_subdir_check_box = self.get_check_box()

        self.copy_unhandled_files_label = QLabel("复制无法处理的文件: ")
        self.copy_unhandled_files_check_box = self.get_check_box()

        self.image_max_width_label = QLabel("图片最大宽度: ")
        self.image_max_width_combo_box = self.get_combo_box(["1024", "2048"], 0)

        self.num_processes_label = QLabel("进程数: ")
        self.num_processes_combo_box = self.get_combo_box(["1"], 0)
        self.start_btn = self.get_action_btn("开始压缩", self.start)
        self.stop_btn = self.get_action_btn("停止压缩", self.stop)
        self.stop_btn.setHidden(True)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setHidden(True)

        self.status_label = QLabel("状态栏", self)
        self.status_bar = QStatusBar(self)
        self.status_bar.addWidget(self.status_label)
        self.setup_grid_layout()

    def setup_grid_layout(self):
        """Set up the grid layout of the main window

        there are 12 columns and many rows in the layout
        """
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(self.input_dir_label, 0, 0)
        grid.addWidget(self.input_dir_line_edit, 0, 1, 1, 10)
        grid.addWidget(self.input_dir_browse_btn, 0, 11)

        grid.addWidget(self.output_dir_label, 1, 0)
        grid.addWidget(self.output_dir_line_edit, 1, 1, 1, 10)
        grid.addWidget(self.output_dir_browse_btn, 1, 11)

        grid.addWidget(self.include_subdir_label, 2, 0)
        grid.addWidget(self.include_subdir_check_box, 2, 1)

        grid.addWidget(self.copy_unhandled_files_label, 2, 2)
        grid.addWidget(self.copy_unhandled_files_check_box, 2, 3)

        grid.addWidget(self.start_btn, 3, 11, 2, 1)
        grid.addWidget(self.stop_btn, 3, 11, 2, 1)
        grid.addWidget(self.image_max_width_label, 3, 0)
        grid.addWidget(self.image_max_width_combo_box, 3, 1)

        grid.addWidget(self.num_processes_label, 4, 0)
        grid.addWidget(self.num_processes_combo_box, 4, 1)

        grid.addWidget(self.progress_bar, 5, 0, 1, 12)

        grid.addWidget(self.status_bar, 6, 0, 1, 12)
        self.setLayout(grid)
        self.center_window()

    def get_action_btn(self, text: str, slot: Callable) -> QPushButton:
        """get start button with default attributes"""
        btn = QPushButton(text)
        btn.clicked.connect(slot)
        # default button height 32 x 2
        btn.setFixedHeight(64)
        return btn

    def get_dir_line_edit(self, default: Path) -> DirLineEdit:
        """get DirLineEdit() with default attributes"""
        line_edit = DirLineEdit()
        line_edit.setDragEnabled(True)
        line_edit.setReadOnly(True)
        line_edit.setEnabled(False)
        line_edit.setText(str(default.resolve()))
        return line_edit

    def get_browse_dir_btn(self, edit: QLineEdit) -> QPushButton:
        """get button to open browse directory dialog

        Args:
            edit: QLineEdit to display the selected directory
        """
        btn = QPushButton("浏览...")
        btn.clicked.connect(lambda: self.on_browse_dir_btn_pressed(edit))
        return btn

    def on_browse_dir_btn_pressed(self, edit: QLineEdit):
        """open dialog to browse directory

        Args:
            edit: QLineEdit to display the selected directory
        """
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择文件夹",
            edit.text(),
        )
        if folder:
            edit.setText(folder)

    def get_check_box(self):
        """get check box with default attributes

        NOTE:
        the check box is only used to display the configuration of the program,
        changing the configuration has not been implemented yet
        """
        check_box = QCheckBox()
        check_box.setChecked(True)
        check_box.setEnabled(False)
        return check_box

    def get_combo_box(self, items: list[str], current_index: int) -> QComboBox:
        """get combo box with default attributes

        Args:
            items: items to display in the combo box
            current_index: index of the current item
        """
        combo_box = QComboBox()
        combo_box.addItems(items)
        combo_box.setCurrentIndex(current_index)
        return combo_box

    def center_window(self):
        """center window on screen

        Refs:
            https://zetcode.com/pyqt6/firstprograms/
        """
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()

        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def closeEvent(self, event):
        """called when the window is closed (press the X button)"""
        print("quiting")

    def on_progress_change(self, progress: int):
        self.progress_bar.setValue(progress)

    def start(self):
        # windows GUI fix
        multiprocessing.freeze_support()
        # add tasks to the queue
        tasks_list = compressor.get_tasks_list(
            input_dir=Path(self.input_dir_line_edit.text()),
            output_dir=Path(self.output_dir_line_edit.text()),
        )
        for task in tasks_list:
            self.tasks.put(task)
        # update the UI when the workers start
        self.progress_bar.setHidden(False)
        self.progress_bar.setMaximum(len(tasks_list))
        self.progress_bar.reset()
        self.start_btn.setHidden(True)
        self.stop_btn.setHidden(False)
        self.status_label.setText("正在转换...")
        # start worker
        start_thread = StartThread(
            num_processes=int(self.num_processes_combo_box.currentText()),
            tasks=self.tasks,
            max_width=int(self.image_max_width_combo_box.currentText()),
            counter=self.counter,
        )
        start_thread.progress.connect(self.on_progress_change)
        # update the UI when the worker is finished
        self.start_btn.setHidden(False)
        self.stop_btn.setHidden(True)
        self.status_label.setText("已完成")

    def stop(self):
        self.start_btn.setHidden(False)
        self.stop_btn.setHidden(True)
        self.status_label.setText("已停止")


def app():
    """start the application"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon("./resources/icon.png"))
    window = MainWindow()
    window.setWindowTitle("图片批量压缩工具")
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    app()
