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

from bit_manipulation import lsb_interleave_list, lsb_deinterleave_list
from bit_manipulation import roundup
import getopt
import os
from PIL import Image
import sys
from time import time


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


def hide_data(input_image_path, input_file_path, steg_image_path, num_lsb,
              compression_level):
    """Hides the data from the input file in the input image."""
    print("Reading files...".ljust(30), end='', flush=True)
    start = time()
    image, input_file = prepare_hide(input_image_path, input_file_path)
    num_channels = len(image.getdata()[0])
    flattened_color_data = [v for t in image.getdata() for v in t]

    # We add the size of the input file to the beginning of the payload.
    file_size = get_filesize(input_file_path)
    file_size_tag = file_size.to_bytes(bytes_in_max_file_size(image, num_lsb),
                                       byteorder=sys.byteorder)

    data = file_size_tag + input_file.read()
    print("Done in {:.2f} s".format(time() - start))

    if 8 * len(data) > max_bits_to_hide(image, num_lsb):
        print("Only able to hide", max_bits_to_hide(image, num_lsb) // 8,
              "B in image. PROCESS WILL FAIL!")

    print("Hiding {} bytes...".format(file_size).ljust(30), end='', flush=True)
    start = time()
    flattened_color_data = lsb_interleave_list(flattened_color_data, data,
                                               num_lsb)
    print("Done in {:.2f} s".format(time() - start))

    print("Writing to output image...".ljust(30), end='', flush=True)
    start = time()
    # PIL expects a sequence of tuples, one per pixel
    image.putdata(list(zip(*[iter(flattened_color_data)] * num_channels)))
    image.save(steg_image_path, compress_level=compression_level)
    print("Done in {:.2f} s".format(time() - start))


def recover_data(steg_image_path, output_file_path, num_lsb):
    """Writes the data from the steganographed image to the output file"""
    print("Reading files...".ljust(30), end='', flush=True)
    start = time()
    steg_image, output_file = prepare_recover(steg_image_path,
                                              output_file_path)

    color_data = [v for t in steg_image.getdata() for v in t]

    file_size_tag_size = bytes_in_max_file_size(steg_image, num_lsb)
    tag_bit_height = roundup(8 * file_size_tag_size / num_lsb)

    bytes_to_recover = int.from_bytes(
        lsb_deinterleave_list(color_data[:tag_bit_height],
                              8 * file_size_tag_size, num_lsb),
        byteorder=sys.byteorder)
    print("Done in {:.2f} s".format(time() - start))

    print("Recovering {} bytes".format(bytes_to_recover).ljust(30),
          end='', flush=True)
    start = time()
    data = lsb_deinterleave_list(color_data[tag_bit_height:],
                                 8 * bytes_to_recover, num_lsb)
    print("Done in {:.2f} s".format(time() - start))

    print("Writing to output file...".ljust(30), end='', flush=True)
    start = time()
    output_file.write(data)
    output_file.close()
    print("Done in {:.2f} s".format(time() - start))


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
                    bytes_in_max_file_size(image, num_lsb)))


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
