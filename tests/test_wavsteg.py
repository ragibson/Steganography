import numpy as np
import os
from random import choice
from stego_lsb.WavSteg import hide_data, recover_data
import string
from typing import Any, Type
import unittest
import wave


class TestWavSteg(unittest.TestCase):
    def write_random_wav(self, filename: str, num_channels: int, sample_width: int, framerate: int,
                         num_frames: int) -> None:
        if sample_width != 1 and sample_width != 2:
            # WavSteg doesn't support higher sample widths
            raise ValueError("File has an unsupported bit-depth")

        file = wave.open(filename, "w")
        file.setnchannels(num_channels)
        file.setsampwidth(sample_width)
        file.setframerate(framerate)

        dtype: Type[np.unsignedinteger[Any]]
        if sample_width == 1:
            dtype = np.uint8
        else:
            dtype = np.uint16

        data = np.random.randint(0, 2 ** (8 * sample_width), dtype=dtype, size=num_frames * num_channels)
        # note: typing does not recognize that "writeframes() accepts any bytes-like object" (see documentation)
        file.writeframes(data)  # type: ignore

    def write_random_file(self, filename: str, num_bytes: int) -> None:
        with open(filename, "wb") as file:
            file.write(os.urandom(num_bytes))

    def check_random_interleaving(self, byte_depth: int = 1, num_trials: int = 256, filename_length: int = 5) -> None:
        filename = "".join(choice(string.ascii_lowercase) for _ in range(filename_length))
        wav_input_filename = filename + ".wav"
        payload_input_filename = filename + ".txt"
        wav_output_filename = filename + "_steg.wav"
        payload_output_filename = filename + "_recovered.txt"

        np.random.seed(0)
        for _ in range(num_trials):
            num_channels = np.random.randint(1, 64)
            num_frames = np.random.randint(1, 16384)
            num_lsb = np.random.randint(1, 8 * byte_depth + 1)
            payload_len = (num_frames * num_lsb * num_channels) // 8

            self.write_random_wav(wav_input_filename, num_channels=num_channels, sample_width=byte_depth,
                                  framerate=44100, num_frames=num_frames)
            self.write_random_file(payload_input_filename, num_bytes=payload_len)

            try:
                hide_data(wav_input_filename, payload_input_filename, wav_output_filename, num_lsb)
                recover_data(wav_output_filename, payload_output_filename, num_lsb, payload_len)
            except ValueError as e:
                os.remove(wav_input_filename)
                os.remove(payload_input_filename)
                os.remove(wav_output_filename)
                os.remove(payload_output_filename)
                raise e

            with open(payload_input_filename, "rb") as input_file, open(payload_output_filename, "rb") as output_file:
                input_payload_data = input_file.read()
                output_payload_data = output_file.read()

            os.remove(wav_input_filename)
            os.remove(payload_input_filename)
            os.remove(wav_output_filename)
            os.remove(payload_output_filename)

            self.assertEqual(input_payload_data, output_payload_data)

    def test_consistency_8bit(self) -> None:
        self.check_random_interleaving(byte_depth=1)

    def test_consistency_16bit(self) -> None:
        self.check_random_interleaving(byte_depth=2)


if __name__ == "__main__":
    unittest.main()
