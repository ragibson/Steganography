# Steganography

# Table of Contents
  * [Installation](#Installation)
  * [Byte Sequence Manipulation](#ByteSequenceManipulation)
  * [WavSteg](#WavSteg)
  * [LSBSteg](#LSBSteg)
  * [StegDetect](#StegDetect)

<a name = "Installation"></a>
## Installation
This project is on [PyPI](https://pypi.org/project/stego-lsb/) and can be
installed with

    pip install stego-lsb

Alternatively, you can install it from this repository directly:

    git clone https://github.com/ragibson/Steganography
    cd Steganography
    python3 setup.py install

<a name = "ByteSequenceManipulation"></a>
## Byte Sequence Manipulation
bit_manipulation provides the ability to (quickly) interleave the bytes of a
payload directly in the least significant bits of a carrier byte sequence.

Specifically, it contains four primary functions:

    # Interleave the bytes of payload into the num_lsb LSBs of carrier.
    lsb_interleave_bytes(carrier, payload, num_lsb, truncate=False)

    # Deinterleave num_bits bits from the num_lsb LSBs of carrier.
    lsb_deinterleave_bytes(carrier, num_bits, num_lsb)

    # Runs lsb_interleave_bytes with a List[uint8] carrier.
    lsb_interleave_list(carrier, payload, num_lsb)

    # Runs lsb_deinterleave_bytes with a List[uint8] carrier.
    lsb_deinterleave_list(carrier, num_bits, num_lsb)

Running `bit_manipulation.py`, calling its `test()` function directly, or
running `stegolsb test` should produce output similar to

    Testing 1.0 MB payload -> 10.0 MB carrier...
    Progress: [################################]
    ----------------------------------------
    | # LSBs | Encode Rate  | Decode rate  |
    | 1      | 40.1   MB/s  | 56.3   MB/s  |
    | 2      | 56.6   MB/s  | 52.7   MB/s  |
    | 3      | 82.5   MB/s  | 77.4   MB/s  |
    | 4      | 112.4  MB/s  | 105.9  MB/s  |
    | 5      | 135.9  MB/s  | 129.8  MB/s  |
    | 6      | 159.9  MB/s  | 152.4  MB/s  |
    | 7      | 181.7  MB/s  | 174.6  MB/s  |
    | 8      | 372.8  MB/s  | 902.8  MB/s  |
    ----------------------------------------

<a name = "WavSteg"></a>
## WavSteg
WavSteg uses least significant bit steganography to hide a file in the samples
of a .wav file.

For each sample in the audio file, we overwrite the least significant bits with
the data from our file.

### How to use
WavSteg requires Python 3

Run WavSteg with the following command line arguments:

    Command Line Arguments:
     -h, --hide               To hide data in a sound file
     -r, --recover            To recover data from a sound file
     -i, --input TEXT         Path to a .wav file
     -s, --secret TEXT        Path to a file to hide in the sound file
     -o, --output TEXT        Path to an output file
     -n, --lsb-count INTEGER  How many LSBs to use  [default: 2]
     -b, --bytes INTEGER      How many bytes to recover from the sound file
     --help                   Show this message and exit.

Example:

    $ stegolsb wavsteg -h -i sound.wav -s file.txt -o sound_steg.wav -n 1
    # OR
    $ stegolsb wavsteg -r -i sound_steg.wav -o output.txt -n 1 -b 1000

### Hiding Data
Hiding data uses the arguments -h, -i, -s, -o, and -n.

The following command would hide the contents of file.txt into sound.wav and
save the result as sound_steg.wav. The command also outputs how many bytes have
been used out of a theoretical maximum.

Example:

    $ stegolsb wavsteg -h -i sound.wav -s file.txt -o sound_steg.wav -n 2
    Using 2 LSBs, we can hide 6551441 bytes
    Files read                     in 0.01s
    5589889 bytes hidden           in 0.24s
    Output wav written             in 0.03s

If you attempt to hide too much data, WavSteg will print the minimum number of
LSBs required to hide your data.

### Recovering Data
Recovering data uses the arguments -r, -i, -o, -n, and -b

The following command would recover the hidden data from sound_steg.wav and
save it as output.txt. This requires the size in bytes of the hidden data to
be accurate or the result may be too short or contain extraneous data.

Example:

    $ stegolsb wavsteg -r -i sound_steg.wav -o output.txt -n 2 -b 5589889
    Files read                     in 0.02s
    Recovered 5589889 bytes        in 0.18s
    Written output file            in 0.00s

<a name = "LSBSteg"></a>
## LSBSteg
LSBSteg uses least significant bit steganography to hide a file in the color
information of an RGB image (.bmp or .png).

For each color channel (R,G,B) in each pixel of the image, we overwrite the
least significant bits of the color value with the data from our file.
In order to make recovering this data easier, we also hide the file size
of our input file in the first few color channels of the image.

### How to use
You need Python 3 and Pillow, a fork of the Python Imaging Library (PIL).

Run LSBSteg with the following command line arguments:

    Command Line Arguments:
     -h, --hide                      To hide data in an image file
     -r, --recover                   To recover data from an image file
     -a, --analyze                   Print how much data can be hidden within an image   [default: False]
     -i, --input TEXT                Path to an bitmap (.bmp or .png) image
     -s, --secret TEXT               Path to a file to hide in the image
     -o, --output TEXT               Path to an output file
     -n, --lsb-count INTEGER         How many LSBs to use  [default: 2]
     -c, --compression INTEGER RANGE
                                     1 (best speed) to 9 (smallest file size)  [default: 1]
     --help                          Show this message and exit.

Example:

    $ stegolsb steglsb -a -i input_image.png -s input_file.zip -n 2
    # OR
    $ stegolsb steglsb -h -i input_image.png -s input_file.zip -o steg.png -n 2 -c 1
    # OR
    $ stegolsb steglsb -r -i steg.png -o output_file.zip -n 2

### Analyzing
Before hiding data in an image, it can useful to see how much data can be
hidden. The following command will achieve this, producing output similar to

    $ stegolsb steglsb -a -i input_image.png -s input_file.zip -n 2
    Image resolution: (2000, 1100)
    Using 2 LSBs, we can hide:     1650000 B
    Size of input file:            1566763 B
    File size tag:                 3 B

### Hiding Data
The following command will hide data in the input image and write the result to
the steganographed image, producing output similar to

    $ stegolsb steglsb -h -i input_image.png -s input_file.zip -o steg.png -n 2 -c 1
    Files read                     in 0.26s
    1566763 bytes hidden           in 0.31s
    Image overwritten              in 0.27s

### Recovering Data
The following command will recover data from the steganographed image and write
the result to the output file, producing output similar to

    $ stegolsb steglsb -r -i steg.png -o output_file.zip -n 2
    Files read                     in 0.30s
    1566763 bytes recovered        in 0.28s
    Output file written            in 0.00s

<a name = "StegDetect"></a>
## StegDetect
StegDetect provides one method for detecting simple steganography in images.

### How to Use
You need Python 3 and Pillow, a fork of the Python Imaging Library (PIL).

Run StegDetect with the following command line arguments:

    Command Line Arguments:
     -i, --input TEXT         Path to an image
     -n, --lsb-count INTEGER  How many LSBs to display  [default: 2]
     --help                   Show this message and exit.

### Showing the Least Significant Bits of an Image
We sum the least significant n bits of the RGB color channels for each pixel
and normalize the result to the range 0-255. This value is then applied to each
color channel for the pixel. Where n is the number of least significant bits to
show, the following command will save the resulting image, appending "_nLSBs"
to the file name, and will produce output similar to the following:

    $ stegolsb stegdetect -i input_image.png -n 2
    Runtime: 0.63s
