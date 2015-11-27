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
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from PIL import Image
import os
import timeit

image_path = "image_path.png"

def show_LSB(n):
    # Shows the n least significant bits of image
    start = timeit.default_timer()
    try:
        image = Image.open(image_path)
    except NameError:
        print("Cannot find image")
    
    # Used to set everything but the least significant n bits to 0 when
    # using bitwise AND on an integer
    mask = ((1 << n) - 1)
    
    color_data = list(image.getdata())
    for i in range (len(color_data)):
        rgb = list(color_data[i])
        for j in range(3):
            rgb[j] &= mask
        combined_LSBs = sum(rgb[:3]) * 255 // (3 * mask)
        color_data[i] = tuple((combined_LSBs, combined_LSBs, combined_LSBs))
    
    image.putdata(color_data)
    stop = timeit.default_timer()
    print("Runtime: {0:.2f} s".format(stop - start))
    file_name, file_extension = os.path.splitext(image_path)
    image.save(file_name + "_{}LSBs".format(n) + file_extension)
    image.show()