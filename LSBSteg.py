# The MIT License (MIT)
# 
# Copyright (c) 2015 Ryan Gibson
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import getopt
import math
import os
from PIL import Image
import struct
import sys
import timeit


class Buffer:
    def __init__(self):
        self.buffer = 0
        self.length = 0

    def __len__(self):
        return self.length

    def read_bits(self, n):
        """Removes the first n bits from the buffer and returns them."""
        bits = self.buffer % (1 << n)
        self.buffer >>= n
        self.length -= min(n, self.length)
        return bits

    def __iadd__(self, other):
        self.buffer += other
        return self

    def add_length(self, length):
        self.length += length


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


def and_mask(index, n):
    """Returns an int used to set n bits to 0 from the indexth bit when using
    bitwise AND on an integer of 8 bits or less.
    Ex: and_mask(3,2) --> 0b11100111 = 231."""
    return 255 - ((1 << n) - 1 << index)


def get_filesize(path):
    """Returns the file size in bytes of the file at path"""
    return os.stat(path).st_size


def max_bits_to_hide(image, num_lsb):
    """Returns the number of bits we're able to hide in the image using
    num_lsb least significant bits."""
    # 3 color channels per pixel, num_lsb bits per color channel.
    return int(3 * image.size[0] * image.size[1] * num_lsb)


def bits_in_max_file_size(image, num_lsb):
    """Returns the number of bits needed to store the size of the file."""
    return max_bits_to_hide(image, num_lsb).bit_length()


def hide_data(input_image_path, input_file_path, steg_image_path, num_lsb,
              compression_level):
    """Hides the data from the input file in the input image."""
    start = timeit.default_timer()
    image, input_file = prepare_hide(input_image_path, input_file_path)
    buffer = Buffer()

    data = iter(memoryview(input_file.read()))

    color_data = list(image.getdata())
    color_data_index = 0

    # We add the size of the input file to the beginning of the buffer.
    input_file_size = get_filesize(input_file_path)
    buffer += input_file_size
    buffer.add_length(bits_in_max_file_size(image, num_lsb))

    print("Hiding", input_file_size, "bytes")

    if input_file_size * 8 + len(buffer) > max_bits_to_hide(image, num_lsb):
        print("Only able to hide", max_bits_to_hide(image, num_lsb) // 8,
              "B in image. PROCESS WILL FAIL!")
    mask = and_mask(0, num_lsb)

    done = False
    while not done:
        rgb = list(color_data[color_data_index])
        for i in range(3):
            if len(buffer) < num_lsb:
                # If we need more data in the buffer, add a byte from the
                # file to it.
                try:
                    buffer += next(data) << len(buffer)
                    buffer.add_length(8)
                except StopIteration:
                    # If we've reached the end of our data, we're done
                    done = True
            # Replace the num_lsb least significant bits of each color
            # channel with the first num_lsb bits from the buffer.
            rgb[i] &= mask
            rgb[i] |= buffer.read_bits(num_lsb)
        color_data[color_data_index] = tuple(rgb)
        color_data_index += 1

    image.putdata(color_data)
    image.save(steg_image_path, compress_level=compression_level)
    stop = timeit.default_timer()
    print("Runtime: {0:.2f} s".format(stop - start))


def recover_data(steg_image_path, output_file_path, num_lsb):
    """Writes the data from the steganographed image to the output file"""
    start = timeit.default_timer()
    steg_image, output_file = prepare_recover(steg_image_path,
                                              output_file_path)
    buffer = Buffer()

    data = bytearray()

    color_data = list(steg_image.getdata())
    color_data_index = 0

    pixels_used_for_file_size = int(
        math.ceil(bits_in_max_file_size(steg_image, num_lsb) / (3 * num_lsb)))
    for i in range(pixels_used_for_file_size):
        rgb = list(color_data[color_data_index])
        color_data_index += 1
        for j in range(3):
            # Add the num_lsb least significant bits
            # of each color channel to the buffer.
            buffer += (rgb[j] % (1 << num_lsb) << len(buffer))
            buffer.add_length(num_lsb)

    # Get the size of the file we need to recover.
    bytes_to_recover = buffer.read_bits(
        bits_in_max_file_size(steg_image, num_lsb))
    print("Looking to recover", bytes_to_recover, "bytes")

    while bytes_to_recover > 0:
        rgb = list(color_data[color_data_index])
        color_data_index += 1
        for i in range(3):
            # Add the num_lsb least significant bits
            # of each color channel to the buffer.
            buffer += (rgb[i] % (1 << num_lsb)) << len(buffer)
            buffer.add_length(num_lsb)

        while len(buffer) >= 8 and bytes_to_recover > 0:
            # If we have more than a byte in the buffer, add it to data
            # and decrement the number of bytes left to recover.
            bits = buffer.read_bits(8)
            data += struct.pack('1B', bits)
            bytes_to_recover -= 1

    output_file.write(bytes(data))
    output_file.close()

    stop = timeit.default_timer()
    print("Runtime: {0:.2f} s".format(stop - start))


def analysis(image_file_path, input_file_path, num_lsb):
    """Print how much data we can hide and the size of the data to be hidden"""
    image = Image.open(image_file_path)
    print("Image resolution: ({}, {})\n"
          "Using {} LSBs, we can hide:\t{} B\n"
          "Size of input file:\t\t{} B\n"
          "File size tag:\t\t\t{} B"
          "".format(image.size[0], image.size[1], num_lsb,
                    max_bits_to_hide(image, num_lsb) // 8,
                    get_filesize(input_file_path),
                    math.ceil(bits_in_max_file_size(image, num_lsb) / 8)))


def usage():
    print("\nCommand Line Arguments:\n",
          "-h, --hide           To hide data in an image\n",
          "-r, --recover        To recover data from an image\n",
          "-a, --analyze        Print how much data can be hidden in image\n",
          "-i, --image=         Path to a bitmap (.bmp or .png) image\n",
          "-f, --file=          Path to a file to hide in the image\n",
          "-o, --output=        Path to an output file\n",
          "-n, --LSBs=          How many LSBs to use\n",
          "-c, --compression=   1 (best speed) to 9 (smallest file size)\n",
          "--help               Display this message\n")


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hrai:f:o:n:c:',
                                   ['hide', 'recover', 'analyze', 'image=',
                                    'file=', 'output=', 'LSBs=',
                                    'compression=', 'help'])
    except getopt.GetoptError:
        usage()
        sys.exit(1)

    hiding_data = False
    recovering_data = False
    analyze = False

    # file paths for input, image, and output files
    image_fp = ""
    input_fp = ""
    output_fp = ""

    # number of least significant bits to alter when hiding/recovering data
    num_bits = 2

    # compression level ranging from 1 (best speed) to 9 (smallest file size)
    compression = 1

    for opt, arg in opts:
        if opt in ("-h", "--hide"):
            hiding_data = True
        elif opt in ("-r", "--recover"):
            recovering_data = True
        elif opt in ("-a", "--analyze"):
            analyze = True
        elif opt in ("-i", "--image"):
            image_fp = arg
        elif opt in ("-f", "--file"):
            input_fp = arg
        elif opt in ("-o", "--output"):
            output_fp = arg
        elif opt in ("-n", "--LSBs="):
            num_bits = int(arg)
        elif opt in ("-c", "--compression="):
            compression = int(arg)
        elif opt == "--help":
            usage()
            sys.exit(1)
        else:
            print("Invalid argument {}".format(opt))

    try:
        if analyze:
            analysis(image_fp, input_fp, num_bits)
        if hiding_data:
            hide_data(image_fp, input_fp, output_fp, num_bits, compression)
        if recovering_data:
            recover_data(image_fp, output_fp, num_bits)
    except Exception as e:
        print("Ran into an error during execution.\n",
              "Check input and try again.\n")
        print(e)
        usage()
        sys.exit(1)
