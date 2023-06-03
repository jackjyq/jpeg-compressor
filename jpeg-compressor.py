import logging
import multiprocessing
import shutil
import time
from multiprocessing.synchronize import Lock
from pathlib import Path
from queue import Empty

from PIL import Image
from tqdm import tqdm


def get_logger(filename: str) -> logging.Logger:
    """get logger for the subprocesses

    NOTE: the function should be called in every subprocess, not in main process

    """
    logger: logging.Logger = multiprocessing.get_logger()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(filename)
    handler.setFormatter(
        logging.Formatter(
            f"%(asctime)s - {multiprocessing.current_process().name} - %(message)s"
        )
    )
    logger.addHandler(handler)
    return logger


def log_with_lock(
    *,
    lock: Lock,
    logger: logging.Logger,
    message: str,
):
    """log with lock, to avoid mess up the log file"""
    lock.acquire()
    try:
        logger.info(message)
    finally:
        lock.release()


def increment_with_lock(counter):
    """increase the counter by 1 with lock"""
    with counter.get_lock():
        counter.value += 1


def show_progress(
    *, num_tasks: int, counter, processes: list[multiprocessing.Process]
) -> None:
    UPDATE_DELAY_SECONDES = 1
    pbar = tqdm(total=num_tasks)
    while any(p.is_alive() for p in processes):
        pbar.update(counter.value - pbar.n)  # type: ignore
        time.sleep(UPDATE_DELAY_SECONDES)
    pbar.update(counter.value - pbar.n)  # type: ignore
    pbar.close()


def main(
    *, input_dir: Path, output_dir: Path, num_workers: int, max_width: int
) -> None:
    """start multiprocessing to compress jpg files"""
    # macos fix
    multiprocessing.set_start_method("fork")
    # windows GUI fix
    multiprocessing.freeze_support()
    # compress and save jpeg files by multi-process
    log_lock = multiprocessing.Lock()
    progress_counter = multiprocessing.Value("i", 0)
    num_tasks, tasks = prepare_tasks(input_dir=input_dir, output_dir=output_dir)
    processes = []
    for _ in range(num_workers):
        p: multiprocessing.Process = multiprocessing.Process(
            target=compress_and_save_many,
            kwargs={
                "lock": log_lock,
                "counter": progress_counter,
                "tasks": tasks,
                "max_width": max_width,
            },
        )
        processes.append(p)
        p.start()
    show_progress(num_tasks=num_tasks, counter=progress_counter, processes=processes)
    # wait to finish
    for p in processes:
        p.join()
    print("All done!")


def compress_and_save_many(
    *,
    lock: Lock,
    counter,
    tasks: multiprocessing.Queue,
    max_width: int,
):
    """loop and read tasks from queue and compress and save the images"""
    logger = get_logger(filename="jpeg-compressor.log")
    try:
        # wait timeout to avoid blocking
        while task := tasks.get(timeout=1):
            compress_and_save_one(
                input_file=task[0],
                output_file=task[1],
                max_width=max_width,
                logger=logger,
                lock=lock,
            )
            increment_with_lock(counter)
    except Empty:
        log_with_lock(
            lock=lock, logger=logger, message="Process exist due to empty queue"
        )


def compress_and_save_one(
    *,
    input_file: Path,
    output_file: Path,
    max_width: int,
    logger: logging.Logger,
    lock: Lock,
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
            width *= resize_ratio
            height *= resize_ratio
            image = image.resize(size=(int(width), int(height)), resample=Image.LANCZOS)
            try:
                image.save(output_file, "JPEG", optimize=True, quality=95)
                log_with_lock(
                    lock=lock,
                    logger=logger,
                    message=f"Compressed {input_file} to {output_file}",
                )
                return
            except OSError:
                pass
    shutil.copy(input_file, output_file)
    log_with_lock(
        lock=lock,
        logger=logger,
        message=f"Copied {input_file} to {output_file}",
    )


def prepare_tasks(
    *, input_dir: Path, output_dir: Path
) -> tuple[int, multiprocessing.Queue]:
    """prepare files to be compressed

    Args:
        input_dir (Path): input directory
        output_dir (Path): output directory

    Returns:
        num_tasks (int): total number of files to be compressed
        tasks(Queue): a queue of (input file, output file) tuples
    """

    def get_output_file(input_file: Path) -> Path:
        return output_dir / input_file.relative_to(input_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    tasks_list: list[tuple[Path, Path]] = [
        (input_file, get_output_file(input_file))
        for input_file in input_dir.rglob("*.*")
        if not get_output_file(input_file).exists()
    ]
    tasks: multiprocessing.Queue = multiprocessing.Queue()
    for task in tasks_list:
        tasks.put(task)
    return len(tasks_list), tasks


if __name__ == "__main__":
    main(
        input_dir=Path("/Volumes/SanDisk SSD/jackjyq/Documents/Takeout"),
        output_dir=Path("/Volumes/SanDisk SSD/jackjyq/Documents/compressed"),
        num_workers=4,
        max_width=1920,
    )
