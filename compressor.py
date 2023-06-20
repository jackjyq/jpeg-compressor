import multiprocessing
import shutil
from multiprocessing.synchronize import Lock
from pathlib import Path
from queue import Empty

from PIL import Image


def increment_with_lock(counter):
    """increase the counter by 1 with lock"""
    with counter.get_lock():
        counter.value += 1


def compress_and_save_many(
    *,
    counter,
    tasks: multiprocessing.Queue,
    max_width: int,
):
    """loop and read tasks from queue and compress and save the images"""
    try:
        # wait timeout to avoid blocking
        while task := tasks.get(timeout=1):
            compress_and_save_one(
                input_file=task[0],
                output_file=task[1],
                max_width=max_width,
            )
            increment_with_lock(counter)
    except Empty:
        return


def compress_and_save_one(
    *,
    input_file: Path,
    output_file: Path,
    max_width: int,
) -> None:
    """try to compress jpeg of input_file and save to output_file

    the input image will be copied to output file if it can not be compressed, such as:
        - the input file is not jpg
        - the input file width is less than max_width
        - the output file can not be saved as jpg (e.g. has an alpha channel)

    Args:
        input_file (Path): input file path
        output_file (Path): output file path
        max_width (int): max width of the output image

    Refs:
        https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-filtershttps://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-filters
        https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#jpeg-saving
    """
    SUFFIXES: set[str] = {".jpg", ".jpeg", ".JPG", ".JPEG"}
    output_file.parent.mkdir(parents=True, exist_ok=True)
    if input_file.suffix in SUFFIXES:
        image = Image.open(input_file)
        width, height = image.size
        if width > max_width:
            resize_ratio = max_width / width
            width = int(width * resize_ratio)
            height = int(height * resize_ratio)
            image = image.resize(size=(int(width), int(height)), resample=Image.LANCZOS)
            try:
                image.save(output_file, "JPEG", optimize=True, quality=95)
                return
            except OSError:
                pass
    shutil.copy(input_file, output_file)


def get_tasks_list(*, input_dir: Path, output_dir: Path) -> list[tuple[Path, Path]]:
    """get files to be compressed

    Args:
        input_dir (Path): input directory
        output_dir (Path): output directory

    Returns:
        tasks_list: a list of (input file, output file) tuples
    """

    def get_output_file(input_file: Path) -> Path:
        return output_dir / input_file.relative_to(input_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    return [
        (input_file, get_output_file(input_file))
        for input_file in input_dir.rglob("*.*")
        if not get_output_file(input_file).exists()
    ]
