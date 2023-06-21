import ctypes
import multiprocessing
import sys
import time
from multiprocessing import Queue
from pathlib import Path

from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QCloseEvent, QDragEnterEvent, QDropEvent, QIcon
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


class Worker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(
        self,
        *,
        num_processes: int,
        counter,
        tasks: Queue,
        max_width: int,
        num_tasks: int,
    ) -> None:
        super().__init__()
        self.num_processes = num_processes
        self.counter = counter
        self.tasks = tasks
        self.max_width = max_width
        self.num_tasks = num_tasks

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
        while self.counter.value < self.num_tasks:
            self.progress.emit(self.counter.value)
            time.sleep(0.1)
        for p in processes:
            p.join()
        self.progress.emit(self.counter.value)
        self.finished.emit()


class MainWindow(QWidget):
    def __init__(self):
        """main window of the app"""
        super().__init__()
        # create multi-processes related objects
        self.tasks = multiprocessing.Queue()
        self.counter = multiprocessing.Value("i", 0)
        self.worker_thread = QThread(self)

        # create UI elements
        self.input_dir_label = QLabel("输入文件夹: ")
        self.input_dir_line_edit = self.create_dir_line_edit(
            Path.home().joinpath("Desktop", "input")
        )
        self.input_dir_browse_btn = self.create_browse_dir_btn(self.input_dir_line_edit)

        self.output_dir_label = QLabel("输出文件夹: ")
        self.output_dir_line_edit = self.create_dir_line_edit(
            Path.home().joinpath("Desktop", "output")
        )
        self.output_dir_browse_btn = self.create_browse_dir_btn(
            self.output_dir_line_edit
        )

        self.include_subdir_label = QLabel("包含子文件夹: ")
        self.include_subdir_check_box = self.create_disabled_check_box()

        self.copy_unhandled_files_label = QLabel("复制无法处理的文件: ")
        self.copy_unhandled_files_check_box = self.create_disabled_check_box()

        self.ignore_exist_files_label = QLabel("跳过已存在的文件: ")
        self.ignore_exist_files_check_box = self.create_disabled_check_box()

        self.image_max_width_label = QLabel("图片最大宽度: ")
        self.image_max_width_combo_box = self.create_combo_box(
            ["720", "1080", "2160", "4320"], 2
        )

        self.num_processes_label = QLabel("进程数: ")
        self.num_processes_combo_box = self.create_combo_box(
            [str(n) for n in range(1, multiprocessing.cpu_count() + 1)], 2
        )
        self.action_btn = self.create_action_button()

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setHidden(True)

        self.status_label = QLabel("状态栏", self)
        self.status_bar = QStatusBar(self)
        self.status_bar.addWidget(self.status_label)

        # set up the layout
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

        grid.addWidget(self.copy_unhandled_files_label, 2, 0)
        grid.addWidget(self.copy_unhandled_files_check_box, 2, 1)
        grid.addWidget(self.ignore_exist_files_label, 2, 2)
        grid.addWidget(self.ignore_exist_files_check_box, 2, 3)
        grid.addWidget(self.include_subdir_label, 2, 4)
        grid.addWidget(self.include_subdir_check_box, 2, 5)

        grid.addWidget(self.action_btn, 3, 11, 2, 1)
        grid.addWidget(self.image_max_width_label, 3, 0)
        grid.addWidget(self.image_max_width_combo_box, 3, 1)

        grid.addWidget(self.num_processes_label, 4, 0)
        grid.addWidget(self.num_processes_combo_box, 4, 1)

        grid.addWidget(self.progress_bar, 5, 0, 1, 12)

        grid.addWidget(self.status_bar, 6, 0, 1, 12)
        self.setLayout(grid)
        self.center_window()

    def create_action_button(self) -> QPushButton:
        """get start button with default attributes"""
        btn = QPushButton("开始压缩")
        btn.setCheckable(True)
        btn.clicked.connect(self.on_action_btn_pressed)
        # default button height 32 x 2
        btn.setFixedHeight(64)
        return btn

    def create_dir_line_edit(self, default: Path) -> DirLineEdit:
        """get DirLineEdit() with default attributes"""
        line_edit = DirLineEdit()
        line_edit.setDragEnabled(True)
        line_edit.setReadOnly(True)
        line_edit.setText(str(default.resolve()))
        return line_edit

    def create_browse_dir_btn(self, edit: QLineEdit) -> QPushButton:
        """get button to open browse directory dialog

        Args:
            edit: QLineEdit to display the selected directory
        """
        btn = QPushButton("浏览...")
        btn.clicked.connect(lambda: self.on_browse_dir_btn_pressed(edit))
        return btn

    def create_disabled_check_box(self):
        """get check box with default attributes

        NOTE:
        the check box is only used to display the configuration of the program,
        changing the configuration has not been implemented yet
        """
        check_box = QCheckBox()
        check_box.setChecked(True)
        check_box.setEnabled(False)
        return check_box

    def create_combo_box(self, items: list[str], current_index: int) -> QComboBox:
        """get combo box with default attributes

        Args:
            items: items to display in the combo box
            current_index: index of the current item
        """
        combo_box = QComboBox()
        combo_box.addItems(items)
        combo_box.setCurrentIndex(current_index % len(items))
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
            edit.setText(str(Path(folder).resolve()))

    @pyqtSlot(int)
    def on_progress_change(self, progress: int):
        self.progress_bar.setValue(progress)

    @pyqtSlot()
    def on_worker_finished(self):
        self.status_label.setText("正在停止...")
        self.worker_thread.quit()
        self.worker_thread.wait()
        self.progress_bar.setMaximum(1)
        self.progress_bar.reset()
        self.status_label.setText("已完成")
        self.action_btn.setText("开始压缩")
        self.action_btn.setChecked(False)
        self.action_btn.setEnabled(True)

    def on_action_btn_pressed(self):
        if self.action_btn.isChecked():
            self.action_btn.setText("停止压缩")
            self.start()
        else:
            self.action_btn.setText("开始压缩")
            self.stop()

    def start(self):
        # add tasks to the queue
        self.status_label.setText("正在准备文件列表...")
        self.action_btn.setEnabled(False)
        tasks_list = compressor.get_tasks_list(
            input_dir=Path(self.input_dir_line_edit.text()),
            output_dir=Path(self.output_dir_line_edit.text()),
        )
        for task in tasks_list:
            self.tasks.put(task)
        # reset progress bar
        self.progress_bar.reset()
        self.progress_bar.setMaximum(len(tasks_list))
        self.progress_bar.setHidden(False)
        # start worker
        self.worker_object = Worker(
            num_processes=int(self.num_processes_combo_box.currentText()),
            tasks=self.tasks,
            max_width=int(self.image_max_width_combo_box.currentText()),
            counter=self.counter,
            num_tasks=len(tasks_list),
        )
        self.worker_object.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker_object.run)
        self.worker_object.progress.connect(self.on_progress_change)
        self.worker_object.finished.connect(self.on_worker_finished)
        self.worker_thread.start()
        self.action_btn.setEnabled(True)
        self.status_label.setText("正在压缩...")

    def stop(self):
        self.status_label.setText("正在取消任务...")
        self.action_btn.setEnabled(False)
        self.progress_bar.setHidden(False)
        compressor.clear_tasks(self.tasks, self.counter)

    def closeEvent(self, event: QCloseEvent):
        """override close event

        Args:
            event: close event
        """
        if hasattr(self, "worker_thread") and self.worker_thread.isRunning():
            self.stop()
            event.ignore()
        else:
            event.accept()


def app():
    """start the application"""
    # workaround for windows taskbar icon
    # Refs: https://stackoverflow.com/a/1552105
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("jepg-compressor")
    # windows GUI fix
    multiprocessing.freeze_support()
    # get icon file path (to be compatible with nuitka)
    icon_file: str = str((Path(__file__).parent / "resources" / "icon.ico").resolve())

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon(icon_file))

    window = MainWindow()
    window.setWindowIcon(QIcon(icon_file))
    window.setWindowTitle("图片批量压缩工具")
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    app()
