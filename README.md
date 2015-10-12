# Steganography

# Table of Contents
  * [LSBSteg](#LSBSteg)
  * [StegDetect](#StegDetect)

<a name = "LSBSteg"/>
## LSBSteg
LSBSteg uses least significant bit steganography to hide a file in the color
information of an RGB image (.bmp or .png).

For each color channel (R,G,B) in each pixel of the image, we overwrite the
least significant bits of the color value with the data from our file.
In order to make recovering this data easier, we also hide the filesize
of our input file in the first few color channels of the image.

### How to use
You need Python 3 and Pillow, a fork of the Python Imaging Library (PIL).

Run LSBSteg in interactive mode using one of the following commands:
    
	py -i LSBSteg.py
	# OR
	python -i LSBSteg.py

Set the following variables, depending on what you want to do.

    # Path of the image to hide data in
	# Default is "input_image.png"
	input_image_path = "directory\input_image.png"
	
	# Path of the image to recover data from OR
	# Path to write steganographed image
	# Default is "steg_image.png"
	steg_image_path = "directory\steg_image.png"
	
	# Path of file to hide in image
	# Default is "input.zip"
	input_file_path = "directory\input_file.zip"
	
	# Path of file to recover data to
	# Default is "output.zip"
	output_file_path = "directory\output_file.zip"
	
	# Number of least signifcant bits to use when hiding or recovering data
	# Default is 2
	num_lsb = 2

### Analyzing
Before hiding data in an image, it can useful to see how much data can be hidden.
Using num_lsb, input_image_path, and input_file_path, the command analysis() will
produce output similar to the following:

    >>> analysis()
    Image resolution: ( 2000 , 1100 )
    Using 2 LSBs, we can hide:       1650000 B
    Size of input file:              1566763 B
    Filesize tag:                    3 B
	
### Hiding Data
Using num_lsb, input_image_path, input_file_path, and steg_image_path, we hide
data in the input image and write the result to the steganographed image. The 
command hide_data() will produce output similar to the following:

    >>> hide_data()
    Hiding 1566763 bytes
    Runtime: 7.22 s

### Recovering Data
Using num_lsb, steg_image_path, and output_file_path we recover data from the
steganographed image and write the result to the output file. The command
recover_data() will produce output similar to the following:

    >>> recover_data()
    Looking to recover 1566763 bytes
    Runtime: 4.44 s

<a name = "StegDetect"/>
## StegDetect
StegDetect provides various methods for detecting steganography in images.

### How to Use
You need Python 3 and Pillow, a fork of the Python Imaging Library (PIL).

Run StegDetect in interactive mode using one of the following commands:
    
	py -i StegDetect.py
	# OR
	python -i StegDetect.py
	
Set the image path.

    # Path of the image
	# Default is "image_path.png"
	image_path = "directory\image.png"
	
### Showing the Least Significant Bits of an Image
Using image_path, we sum the least significant n bits of the RGB color channels
for each pixel and normalize the result to the range 0-255. This value is then
applied to each color channel for the pixel. Where n is the number of least
significant bits to show, the command show_LSB(n) will produce output similar to
the following:

    >>> show_LSB(1)
    Runtime: 3.55 s