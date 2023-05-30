# JPEG Compressor

## Quick Start

```shell
python jpeg-compressor.py D:\uncompressed_jpeg D:\compressed_jpeg
```

- tested on Python3.10
- tested on Windows 11

## Read the docs

```shell
python jpeg-compressor.py -h
```

```shell
usage: jpeg-compressor.py [-h] [-w [MAX_WIDTH]] [-n [NUM_WORKERS]] input_dir output_dir

JPEG Compressor
compress jpg images in input_dir recursively and save to output_dir with the same directory structure.

The program will try to only resize the image rather than reduce its quality.

The files in output_dir will be skipped if they already exist. Thus, you can restart the program if it is interrupted.

The files in input_dir will be copied to output_dir if they can not be compressed, such as:
    - the input file is neither a jpg, jpeg, JPG nor JPEG
    - the input file width is less than max_width
    - the output file can not be saved as jpg (usually because it is not a valid jpg file)

----------------------------------------------------------------------------------------

positional arguments:
  input_dir             the directory of the input images.
  output_dir            the directory of the output images.

options:
  -h, --help            show this help message and exit
  -w [MAX_WIDTH], --max-width [MAX_WIDTH]
                        the max width of the output image. Default is 2160 (4K), which should be enough for wallpapers
  -n [NUM_WORKERS], --num-workers [NUM_WORKERS]
                        the number of workers, default is the number of cpu cores.
[INFO/MainProcess] process shutting down
```