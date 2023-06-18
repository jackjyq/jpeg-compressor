import platform
import subprocess

BUILD_DIR = "build"
ICON = r"./resources/icon.png"
FILENAME = "图片批量压缩工具"

if platform.system() == "Windows":
    subprocess.run(
        [
            "python",
            "-m",
            "nuitka",
            "main.py",
            "--show-progress",
            "--onefile",
            "--plugin-enable=pyqt6",
            "--windows-disable-console",
            f"--output-dir={BUILD_DIR}",
            f"--windows-icon-from-ico={ICON}",
            "-o",
            FILENAME,
        ]
    )
elif platform.system() == "Darwin":
    subprocess.run(
        [
            "python",
            "-m",
            "nuitka",
            "main.py",
            "--show-progress",
            "--macos-create-app-bundle",
            "--plugin-enable=pyqt6",
            f"--output-dir={BUILD_DIR}",
            f"--macos-app-icon={ICON}",
            "-o",
            FILENAME,
        ]
    )
else:
    raise NotImplementedError
