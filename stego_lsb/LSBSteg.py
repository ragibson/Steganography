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

from PIL import Image

from stego_lsb.bit_manipulation import (lsb_deinterleave_list,
                                        lsb_interleave_list, roundup)

log = logging.getLogger(__name__)


def prepare_hide(input_image_path, input_file_path):
    """Prepare files for reading and writing for hiding data."""
    image = Image.open(input_image_path)
    input_file = open(input_file_path, "rb")
    return image, input_file


def prepare_recover(steg_image_path, output_file_path):
    """Prepare files for reading and writing for recovering data."""
    steg_image = Image.open(steg_image_path)
    output_file = open(output_file_path, "wb+")
    return steg_image, output_file


def get_filesize(path):
    """Returns the file size in bytes of the file at path"""
    return os.stat(path).st_size


def max_bits_to_hide(image, num_lsb):
    """Returns the number of bits we're able to hide in the image using
    num_lsb least significant bits."""
    # 3 color channels per pixel, num_lsb bits per color channel.
    return int(3 * image.size[0] * image.size[1] * num_lsb)


def bytes_in_max_file_size(image, num_lsb):
    """Returns the number of bits needed to store the size of the file."""
    return roundup(max_bits_to_hide(image, num_lsb).bit_length() / 8)


def hide_message_in_image(input_image, message, num_lsb):
    """Hides the message in the input image and returns the modified
    image object.
    """
    start = time()
    # in some cases the image might already be opened
    if isinstance(input_image, Image.Image):
        image = input_image
    else:
        image = Image.open(input_image)

    num_channels = len(image.getdata()[0])
    flattened_color_data = [v for t in image.getdata() for v in t]

    # We add the size of the input file to the beginning of the payload.
    message_size = len(message)
    file_size_tag = message_size.to_bytes(
        bytes_in_max_file_size(image, num_lsb), byteorder=sys.byteorder
    )
    data = file_size_tag + message
    log.debug(f"Files read \t\tin {time() - start:.2f}s")

    if 8 * len(data) > max_bits_to_hide(image, num_lsb):
        log.debug(
            f"Only able to hide {max_bits_to_hide(image, num_lsb) // 8} bytes ",
            "in image. PROCESS WILL FAIL!",
        )

    start = time()
    flattened_color_data = lsb_interleave_list(
        flattened_color_data, data, num_lsb
    )
    log.debug(f"{message_size} bytes hidden \tin {time() - start:.2f}s")

    start = time()
    # PIL expects a sequence of tuples, one per pixel
    image.putdata(list(zip(*[iter(flattened_color_data)] * num_channels)))
    log.debug(f"Image overwritten \tin {time() - start:.2f}s")
    return image


def hide_data(
    input_image_path,
    input_file_path,
    steg_image_path,
    num_lsb,
    compression_level,
):
    """Hides the data from the input file in the input image."""
    image, input_file = prepare_hide(input_image_path, input_file_path)
    image = hide_message_in_image(image, input_file.read(), num_lsb)
    image.save(steg_image_path, compress_level=compression_level)


def recover_message_from_image(input_image, num_lsb):
    """Returns the message from the steganographed image"""
    start = time()
    if isinstance(input_image, Image.Image):
        steg_image = input_image
    else:
        steg_image = Image.open(input_image)

    color_data = [v for t in steg_image.getdata() for v in t]

    file_size_tag_size = bytes_in_max_file_size(steg_image, num_lsb)
    tag_bit_height = roundup(8 * file_size_tag_size / num_lsb)

    bytes_to_recover = int.from_bytes(
        lsb_deinterleave_list(
            color_data[:tag_bit_height], 8 * file_size_tag_size, num_lsb
        ),
        byteorder=sys.byteorder,
    )
    log.debug(f"Files read \t\tin {time() - start:.2f}s")

    start = time()
    data = lsb_deinterleave_list(
        color_data[tag_bit_height:], 8 * bytes_to_recover, num_lsb
    )
    log.debug(f"{bytes_to_recover} bytes recovered \tin {time() - start:.2f}s")
    return data


def recover_data(steg_image_path, output_file_path, num_lsb):
    """Writes the data from the steganographed image to the output file"""
    steg_image, output_file = prepare_recover(steg_image_path, output_file_path)
    data = recover_message_from_image(steg_image, num_lsb)
    start = time()
    output_file.write(data)
    output_file.close()
    log.debug(f"Output file written \tin {time() - start:.2f}s")


def analysis(image_file_path, input_file_path, num_lsb):
    """Print how much data we can hide and the size of the data to be hidden"""
    image = Image.open(image_file_path)
    print(
        "Image resolution: ({}, {})\n"
        "Using {} LSBs, we can hide:\t{} B\n"
        "Size of input file:\t\t{} B\n"
        "File size tag:\t\t\t{} B"
        "".format(
            image.size[0],
            image.size[1],
            num_lsb,
            max_bits_to_hide(image, num_lsb) // 8,
            get_filesize(input_file_path),
            bytes_in_max_file_size(image, num_lsb),
        )
    )
