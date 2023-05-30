import argparse
import logging
import multiprocessing
import random
import shutil
from pathlib import Path
from pprint import pprint

from PIL import Image

logger = multiprocessing.log_to_stderr()
logger.setLevel(logging.INFO)


def compress_and_save_one(input_file: Path, output_file: Path, max_width: int):
    """compress and save jpg file

    the input image will be copied to output file if it can not be compressed, such as:
        - the input file is not jpg
        - the input file width is less than max_width
        - the output file can not be saved as jpg
        ...

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
                return
            except OSError:
                pass
    shutil.copy(input_file, output_file)


def compress_and_save_many(jobs: list[tuple[Path, Path]], max_width: int = 2160):
    """compress and save many jpg files

    Args:
        job (list[tuple[Path, Path]]): [(input_file, output_file)]
        max_width (int): max width of the output image
    """
    count = 0
    for input_file, output_file in jobs:
        compress_and_save_one(input_file, output_file, max_width)
        count += 1
        if count % 100 == 0:
            logger.info(
                f"processed {count} files, {len(jobs) - count} left for this process"
            )


def get_compress_jobs(
    *, input_dir: Path, output_dir: Path, num_workers: int
) -> list[list[tuple[Path, Path]]]:
    """get compress jobs

    Args:
        input_dir (Path): input directory
        output_dir (Path): output directory
        num_workers (int): number of workers
        max_width (int): max width of the output image
    Returns:
        list[list[tuple[Path, Path]]]: [[(input_file, output_file), ...], ...]
    """

    def get_output_file(input_file: Path) -> Path:
        # print(input_file)
        return output_dir / input_file.relative_to(input_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    jobs_list = [
        (input_file, get_output_file(input_file))
        for input_file in input_dir.rglob("*.*")
        if not get_output_file(input_file).exists()
    ]
    # shuffle the jobs to make sure the jobs are evenly distributed to workers
    random.shuffle(jobs_list)
    jobs_per_worker = len(jobs_list) // num_workers + 1
    jobs = [
        jobs_list[i : i + jobs_per_worker]
        for i in range(0, len(jobs_list), jobs_per_worker)
    ]
    # ensure that we always have num_workers jobs
    for _ in range(num_workers-len(jobs)):
        jobs.append([])
    logger.info(f"total jobs: {len(jobs_list)}, divided into {len(jobs)} lists")
    return jobs


def add_arguments() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="""JPEG Compressor
        
compress jpg images in input_dir recursively and save to output_dir with the same directory structure.

The program will try to only resize the image rather than reduce its quality.

The files in output_dir will be skipped if they already exist. Thus, you can restart the program if it is interrupted.

The files in input_dir will be copied to output_dir if they can not be compressed, such as:
    - the input file is neither a jpg, jpeg, JPG nor JPEG
    - the input file width is less than max_width
    - the output file can not be saved as jpg (usually because it is not a valid jpg file)

----------------------------------------------------------------------------------------
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input_dir",
        nargs=1,
        type=Path,
        help="the directory of the input images.",
    )
    parser.add_argument(
        "output_dir",
        nargs=1,
        type=Path,
        help="the directory of the output images.",
    )
    parser.add_argument(
        "-w",
        "--max-width",
        nargs="?",
        type=int,
        default=2160,
        help="the max width of the output image. "
        "Default is 2160 (4K), which should be enough for wallpapers",
    )
    parser.add_argument(
        "-n",
        "--num-workers",
        nargs="?",
        type=int,
        default=multiprocessing.cpu_count(),
        help="the number of workers, default is the number of cpu cores.",
    )
    return parser


if __name__ == "__main__":
    parser = add_arguments()
    args = parser.parse_args()
    logger.info(args)
    args_list = get_compress_jobs(
        input_dir=args.input_dir[0],
        output_dir=args.output_dir[0],
        num_workers=args.num_workers,
    )
    jobs = []
    for i in range(args.num_workers):
        p = multiprocessing.Process(
            target=compress_and_save_many, args=(args_list[i], args.max_width)
        )
        jobs.append(p)
        p.start()
