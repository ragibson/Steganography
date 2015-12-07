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

import getopt, math, os, struct, sys, wave

def hide_data(sound_path, file_path, output_path, num_lsb):
    # Hide data from the file at file_path in the sound file at sound_path

    sound = wave.open(sound_path, "r")
    
    params = sound.getparams()
    num_channels = sound.getnchannels()
    sample_width = sound.getsampwidth()
    num_frames = sound.getnframes()
    num_samples = num_frames * num_channels
    
    # We can hide up to num_lsb bits in each sample of the sound file
    max_bytes_to_hide = (num_samples * num_lsb) // 8
    filesize = os.stat(file_path).st_size
    
    if (filesize > max_bytes_to_hide):
        required_LSBs = math.ceil(filesize * 8 / num_samples)
        raise ValueError("Input file too large to hide, "
                         "requires {} LSBs, using {}"
                         .format(required_LSBs, num_lsb))
    
    print("Using {} B out of {} B".format(filesize, max_bytes_to_hide))
    
    if (sample_width == 1):  # samples are unsigned 8-bit integers
        fmt = "{}B".format(num_samples)
        # Used to set the least significant num_lsb bits of an integer to zero
        mask = (1 << 8) - (1 << num_lsb)
        # The least possible value for a sample in the sound file is actually
        # zero, but we don't skip any samples for 8 bit depth wav files.
        min_sample = -(1 << 8)
    elif (sample_width == 2):  # samples are signed 16-bit integers
        fmt = "{}h".format(num_samples)
        # Used to set the least significant num_lsb bits of an integer to zero
        mask = (1 << 15) - (1 << num_lsb)
        # The least possible value for a sample in the sound file
        min_sample = -(1 << 15)
    else:
        # Python's wave module doesn't support higher sample widths
        raise ValueError("File has an unsupported bit-depth")
    
    # Put all the samples from the sound file into a list
    raw_data = list(struct.unpack(fmt, sound.readframes(num_frames)))
    sound.close()
    
    input_data = memoryview(open(file_path, "rb").read())
    
    # The number of bits we've processed from the input file
    data_index = 0
    sound_index = 0
    
    # values will hold the altered sound data
    values = []
    buffer = 0
    buffer_length = 0
    done = False
    
    while(not done):
        while (buffer_length < num_lsb and data_index // 8 < len(input_data)):
            # If we don't have enough data in the buffer, add the
            # rest of the next byte from the file to it.
            buffer += (input_data[data_index // 8] >> (data_index % 8)
                        ) << buffer_length
            bits_added = 8 - (data_index % 8)
            buffer_length += bits_added
            data_index += bits_added
            
        # Retrieve the next num_lsb bits from the buffer for use later
        current_data = buffer % (1 << num_lsb)
        buffer >>= num_lsb
        buffer_length -= num_lsb

        while (sound_index < len(raw_data) and
               raw_data[sound_index] == min_sample):
            # If the next sample from the sound file is the smallest possible
            # value, we skip it. Changing the LSB of such a value could cause
            # an overflow and drastically change the sample in the output.
            values.append(struct.pack(fmt[-1], raw_data[sound_index]))
            sound_index += 1

        if (sound_index < len(raw_data)):
            current_sample = raw_data[sound_index]
            sound_index += 1

            sign = 1
            if (current_sample < 0):
                # We alter the LSBs of the absolute value of the sample to
                # avoid problems with two's complement. This also avoids
                # changing a sample to the smallest possible value, which we
                # would skip when attempting to recover data.
                current_sample = -current_sample
                sign = -1

            # Bitwise AND with mask turns the num_lsb least significant bits
            # of current_sample to zero. Bitwise OR with current_data replaces
            # these least significant bits with the next num_lsb bits of data.
            altered_sample = sign * ((current_sample & mask) | current_data)

            values.append(struct.pack(fmt[-1], altered_sample))

        if (data_index // 8 >= len(input_data) and buffer_length <= 0):
            done = True
        
    while(sound_index < len(raw_data)):
        # At this point, there's no more data to hide. So we append the rest of
        # the samples from the original sound file.
        values.append(struct.pack(fmt[-1], raw_data[sound_index]))
        sound_index += 1
    
    sound_steg = wave.open(output_path, "w")
    sound_steg.setparams(params)
    sound_steg.writeframes(b"".join(values))
    sound_steg.close()

def recover_data(sound_path, output_path, num_lsb, bytes_to_recover):
    # Recover data from the file at sound_path to the file at output_path
    
    sound = wave.open(sound_path, "r")
    
    num_channels = sound.getnchannels()
    sample_width = sound.getsampwidth()
    num_frames = sound.getnframes()
    num_samples = num_frames * num_channels
    
    if (sample_width == 1):  # samples are unsigned 8-bit integers
        fmt = "{}B".format(num_samples)
        # The least possible value for a sample in the sound file is actually
        # zero, but we don't skip any samples for 8 bit depth wav files.
        min_sample = -(1 << 8)
    elif (sample_width == 2):  # samples are signed 16-bit integers
        fmt = "{}h".format(num_samples)
        # The least possible value for a sample in the sound file
        min_sample = -(1 << 15)
    else:
        # Python's wave module doesn't support higher sample widths
        raise ValueError("File has an unsupported bit-depth")
    
    # Put all the samples from the sound file into a list
    raw_data = list(struct.unpack(fmt, sound.readframes(num_frames)))
    # Used to extract the least significant num_lsb bits of an integer
    mask = (1 << num_lsb) - 1
    output_file = open(output_path, "wb+")
    
    data = bytearray()
    sound_index = 0 
    buffer = 0
    buffer_length = 0
    
    while (bytes_to_recover > 0):
        
        next_sample = raw_data[sound_index]
        if (next_sample != min_sample):
            # Since we skipped samples with the minimum possible value when
            # hiding data, we do the same here.
            buffer += (abs(next_sample) & mask) << buffer_length
            buffer_length += num_lsb
        sound_index += 1
        
        while (buffer_length >= 8 and bytes_to_recover > 0):
            # If we have more than a byte in the buffer, add it to data
            # and decrement the number of bytes left to recover.
            current_data = buffer % (1 << 8)
            buffer >>= 8
            buffer_length -= 8
            data += struct.pack('1B', current_data)
            bytes_to_recover -= 1

    output_file.write(bytes(data))
    output_file.close()

def usage():
    print("\nCommand Line Arguments:\n",
          "-h, --hide        To hide data in a sound file\n",
          "-r, --recover     To recover data from a sound file\n",
          "-s, --sound=      Path to a .wav file\n",
          "-f, --file=       Path to a file to hide in the sound file\n",
          "-o, --output=     Path to an output file\n",
          "-n, --LSBs=       How many LSBs to use\n",
          "-b, --bytes=      How many bytes to recover from the sound file\n",
          "--help            Display this message\n")

try:
    opts, args = getopt.getopt(sys.argv[1:], 'hrs:f:o:n:b:',
                              ['hide', 'recover', 'sound=', 'file=',
                               'output=', 'LSBs=', 'bytes=', 'help'])
except getopt.GetoptError:
    usage()
    sys.exit(1)

hiding_data = False
recovering_data = False

for opt, arg in opts:
    if opt in ("-h", "--hide"):
        hiding_data = True
    elif opt in ("-r", "--recover"):
        recovering_data = True
    elif opt in ("-s", "--sound"):
        sound_path = arg
    elif opt in ("-f", "--file"):
        file_path = arg
    elif opt in ("-o", "--output"):
        output_path = arg
    elif opt in ("-n", "--LSBs="):
        num_lsb = int(arg)
    elif opt in ("-b", "--bytes="):
        bytes_to_recover = int(arg)
    elif opt in ("--help"):
        usage()
        sys.exit(1)
    else:
        print("Invalid argument {}".format(opt))

try:
    if (hiding_data):
        hide_data(sound_path, file_path, output_path, num_lsb)
    if (recovering_data):
        recover_data(sound_path, output_path, num_lsb, bytes_to_recover)
except Exception as e:
    print("Ran into an error during execution. Check input and try again.\n")
    print(e)
    usage()
    sys.exit(1)