import tkinter as tk
from tkinter import filedialog
import multiprocessing
import cli
from pathlib import Path
from pprint import pprint
import subprocess

MAX_WIDTH_OPTIONS = [
    "768",
    "960",
    "1080",
    "2160",
    "4320",
]
NUM_WORKERS_OPTIONS = [str(n) for n in range(1, 49)]
window = tk.Tk()

# global varibles
global_input_dir = tk.StringVar()
global_output_dir = tk.StringVar()
global_max_width = tk.StringVar(value=MAX_WIDTH_OPTIONS[3])
global_num_workers = tk.StringVar(
    value=NUM_WORKERS_OPTIONS[multiprocessing.cpu_count() - 1]
)


# event handlers
def browse_input_dir():
    filename = filedialog.askdirectory()
    global_input_dir.set(filename)


def browse_output_dir():
    filename = filedialog.askdirectory()
    global_output_dir.set(filename)


def start():
    input_dir = Path(global_input_dir.get())
    output_dir = Path(global_output_dir.get())
    max_width = int(global_max_width.get())
    num_workers = int(global_num_workers.get())
    cli.logger.info(
        f"input_dir: {input_dir}, output_dir: {output_dir}, "
        f"max_width: {max_width}, num_workers: {num_workers}"
    )
    subprocess.call(
        [
            "python",
            "cli.py",
            input_dir.resolve(),
            output_dir.resolve(),
            "--max-width",
            str(max_width),
            "--num-workers",
            str(num_workers),
        ]
    )


# widgets definitions
button_intput_dir = tk.Button(text="输入文件夹", command=browse_input_dir)
lbl_input_dir = tk.Label(textvariable=global_input_dir)
button_output_dir = tk.Button(text="输出文件夹", command=browse_output_dir)
lbl_output_dir = tk.Label(textvariable=global_output_dir)
button_start = tk.Button(text="开始", command=start)
menu_max_width = tk.OptionMenu(window, global_max_width, *MAX_WIDTH_OPTIONS)
menu_num_workers = tk.OptionMenu(window, global_num_workers, *NUM_WORKERS_OPTIONS)

# layout
button_intput_dir.grid(row=0, column=1)
lbl_input_dir.grid(row=0, column=3)
button_output_dir.grid(row=1, column=1)
lbl_output_dir.grid(row=1, column=3)
menu_max_width.grid(row=2, column=1)
menu_num_workers.grid(row=3, column=1)
button_start.grid(row=4, column=1)

window.mainloop()
