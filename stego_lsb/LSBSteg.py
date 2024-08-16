# -*- coding: utf-8 -*-
"""
    stego_lsb.LSBSteg
    ~~~~~~~~~~~~~~~~~

    This module contains functions for hiding and recovering
    data from bitmap (.bmp and .png) files.

    :copyright: (c) 2015 by Ryan Gibson, see AUTHORS.md for more details.
    :license: MIT License, see LICENSE.md for more details.
"""
import logging
import os
import sys
from time import time
from typing import Tuple, IO, Union, List, cast

from PIL import Image

from stego_lsb.bit_manipulation import (
    lsb_deinterleave_list,
    lsb_interleave_list,
    roundup,
)

log = logging.getLogger(__name__)


def _str_to_bytes(x: Union[bytes, str], charset: str = sys.getdefaultencoding(), errors: str = "strict") -> bytes:
    if x is None:
        return None
    if isinstance(x, (bytes, bytearray, memoryview)):  # noqa
        return bytes(x)
    if isinstance(x, str):
        return x.encode(charset, errors)
    if isinstance(x, int):
        return str(x).encode(charset, errors)
    raise TypeError("Expected bytes")


def prepare_hide(input_image_path: str, input_file_path: str) -> Tuple[Image.Image, IO[bytes]]:
    """Prepare files for reading and writing for hiding data."""
    # note that these should be closed! consider using context managers instead
    image = Image.open(input_image_path)
    input_file = open(input_file_path, "rb")
    return image, input_file  # these should be closed after use! Consider using a context manager


def prepare_recover(steg_image_path: str, output_file_path: str) -> Tuple[Image.Image, IO[bytes]]:
    """Prepare files for reading and writing for recovering data."""
    # note that these should be closed! consider using context managers instead
    steg_image = Image.open(steg_image_path)
    output_file = open(output_file_path, "wb+")
    return steg_image, output_file  # these should be closed after use! Consider using a context manager


def get_filesize(path: str) -> int:
    """Returns the file size in bytes of the file at path"""
    return os.stat(path).st_size


def max_bits_to_hide(image: Image.Image, num_lsb: int, num_channels: int) -> int:
    """Returns the number of bits we're able to hide in the image using num_lsb least significant bits."""
    # num_channels color channels per pixel, num_lsb bits per color channel.
    return int(num_channels * image.size[0] * image.size[1] * num_lsb)


def bytes_in_max_file_size(image: Image.Image, num_lsb: int, num_channels: int) -> int:
    """Returns the number of bits needed to store the size of the file."""
    return roundup(max_bits_to_hide(image, num_lsb, num_channels).bit_length() / 8)


def hide_message_in_image(input_image: Image.Image, message: Union[str, bytes], num_lsb: int,
                          skip_storage_check: bool = False) -> Image.Image:
    """Hides the message in the input image and returns the modified image object."""
    start = time()
    num_channels = len(input_image.getbands())
    flattened_color_data = [v for t in input_image.getdata() for v in t]

    # We add the size of the input file to the beginning of the payload.
    message_size = len(message)
    file_size_tag = message_size.to_bytes(bytes_in_max_file_size(input_image, num_lsb, num_channels),
                                          byteorder=sys.byteorder)
    data = file_size_tag + _str_to_bytes(message)
    log.debug(f"{'Files read':<30} in {time() - start:.2f}s")

    if 8 * len(data) > max_bits_to_hide(input_image, num_lsb, num_channels) and not skip_storage_check:
        raise ValueError(f"Only able to hide {max_bits_to_hide(input_image, num_lsb, num_channels) // 8} bytes in "
                         f"this image with {num_lsb} LSBs, but {len(data)} bytes were requested")

    start = time()
    flattened_color_data = lsb_interleave_list(flattened_color_data, data, num_lsb)
    log.debug(f"{f'{message_size} bytes hidden':<30} in {time() - start:.2f}s")

    start = time()
    # PIL expects a sequence of tuples, one per pixel
    input_image.putdata(cast(List[int], list(zip(*[iter(flattened_color_data)] * num_channels))))
    log.debug(f"{'Image overwritten':<30} in {time() - start:.2f}s")
    return input_image


def hide_data(input_image_path: str, input_file_path: str, steg_image_path: str, num_lsb: int,
              compression_level: int, skip_storage_check: bool = False) -> None:
    """Hides the data from the input file in the input image."""
    if input_image_path is None:
        raise ValueError("LSBSteg hiding requires an input image file path")
    if input_file_path is None:
        raise ValueError("LSBSteg hiding requires a secret file path")
    if steg_image_path is None:
        raise ValueError("LSBSteg hiding requires an output image file path")

    image, input_file = prepare_hide(input_image_path, input_file_path)
    with image as image, input_file as input_file:
        image = hide_message_in_image(image, input_file.read(), num_lsb, skip_storage_check=skip_storage_check)

        # just in case is_animated is not defined, as suggested by the Pillow documentation
        is_animated = getattr(image, "is_animated", False)
        image.save(steg_image_path, compress_level=compression_level, save_all=is_animated)


def recover_message_from_image(input_image: Image.Image, num_lsb: int) -> bytes:
    """Returns the message from the steganographed image"""
    start = time()
    num_channels = len(input_image.getbands())
    color_data = [v for t in input_image.getdata() for v in t]

    file_size_tag_size = bytes_in_max_file_size(input_image, num_lsb, num_channels)
    tag_bit_height = roundup(8 * file_size_tag_size / num_lsb)

    bytes_to_recover = int.from_bytes(lsb_deinterleave_list(color_data[:tag_bit_height], 8 * file_size_tag_size,
                                                            num_lsb), byteorder=sys.byteorder)

    maximum_bytes_in_image = (max_bits_to_hide(input_image, num_lsb, num_channels) // 8 - file_size_tag_size)
    if bytes_to_recover > maximum_bytes_in_image:
        raise ValueError(f"This image appears to be corrupted.\nIt claims to hold {bytes_to_recover} B, "
                         f"but can only hold {maximum_bytes_in_image} B with {num_lsb} LSBs")

    log.debug(f"{'Files read':<30} in {time() - start:.2f}s")

    start = time()
    data = lsb_deinterleave_list(color_data, 8 * (bytes_to_recover + file_size_tag_size), num_lsb)[
           file_size_tag_size:]
    log.debug(f"{f'{bytes_to_recover} bytes recovered':<30} in {time() - start:.2f}s")
    return data


def recover_data(steg_image_path: str, output_file_path: str, num_lsb: int) -> None:
    """Writes the data from the steganographed image to the output file"""
    if steg_image_path is None:
        raise ValueError("LSBSteg recovery requires an input image file path")
    if output_file_path is None:
        raise ValueError("LSBSteg recovery requires an output file path")

    steg_image, output_file = prepare_recover(steg_image_path, output_file_path)
    with steg_image as steg_image, output_file as output_file:
        data = recover_message_from_image(steg_image, num_lsb)
        start = time()
        output_file.write(data)
        log.debug(f"{'Output file written':<30} in {time() - start:.2f}s")


def analysis(image_file_path: str, input_file_path: str, num_lsb: int) -> None:
    """Print how much data we can hide and the size of the data to be hidden"""
    if image_file_path is None:
        raise ValueError("LSBSteg analysis requires an input image file path")

    with Image.open(image_file_path) as image:
        num_channels = len(image.getbands())
        print(f"Image resolution: ({image.size[0]}, {image.size[1]}, {len(image.getbands())})\n"
              f"{f'Using {num_lsb} LSBs, we can hide:':<30} {max_bits_to_hide(image, num_lsb, num_channels) // 8} B")

        if input_file_path is not None:
            print(f"{'Size of input file:':<30} {get_filesize(input_file_path)} B")

        print(f"{'File size tag:':<30} {bytes_in_max_file_size(image, num_lsb, num_channels)} B")
