# -*- coding: utf-8 -*-
"""
    stego_lsb.WavSteg
    ~~~~~~~~~~~~~~~~~

    This module contains functions for hiding and retrieving
    data from .wav files.

    :copyright: (c) 2015 by Ryan Gibson, see AUTHORS.md for more details.
    :license: MIT License, see LICENSE.md for more details.
"""
from stego_lsb.bit_manipulation import lsb_deinterleave_bytes, lsb_interleave_bytes
from time import time
import logging
import math
import os
import wave

log = logging.getLogger(__name__)


def hide_data(sound_path: str, file_path: str, output_path: str, num_lsb: int) -> None:
    """Hide data from the file at file_path in the sound file at sound_path"""
    if sound_path is None:
        raise ValueError("WavSteg hiding requires an input sound file path")
    if file_path is None:
        raise ValueError("WavSteg hiding requires a secret file path")
    if output_path is None:
        raise ValueError("WavSteg hiding requires an output sound file path")

    with wave.open(sound_path, "r") as sound:
        params = sound.getparams()
        num_channels = sound.getnchannels()
        sample_width = sound.getsampwidth()
        num_frames = sound.getnframes()
        num_samples = num_frames * num_channels

        # We can hide up to num_lsb bits in each sample of the sound file
        max_bytes_to_hide = (num_samples * num_lsb) // 8
        file_size = os.stat(file_path).st_size

        log.debug(f"Using {num_lsb} LSBs, we can hide {max_bytes_to_hide} bytes")

        start = time()
        sound_frames = sound.readframes(num_frames)
        with open(file_path, "rb") as file:
            data = file.read()
        log.debug(f"{'Files read':<30} in {time() - start:.2f}s")

        if file_size > max_bytes_to_hide:
            required_lsb = math.ceil(file_size * 8 / num_samples)
            raise ValueError(f"Input file too large to hide, requires {required_lsb} LSBs, using {num_lsb}")

        if sample_width < 1 or sample_width > 4:
            # WavSteg doesn't support higher sample widths, see setsampwidth() in cpython/Libwave.py
            raise ValueError("File has an unsupported bit-depth")

        start = time()
        sound_frames = lsb_interleave_bytes(sound_frames, data, num_lsb, byte_depth=sample_width)
        log.debug(f"{f'{file_size} bytes hidden':<30} in {time() - start:.2f}s")

        start = time()
        with wave.open(output_path, "w") as sound_steg:
            sound_steg.setparams(params)
            sound_steg.writeframes(sound_frames)
        log.debug(f"{'Output wav written':<30} in {time() - start:.2f}s")


def recover_data(sound_path: str, output_path: str, num_lsb: int, bytes_to_recover: int) -> None:
    """Recover data from the file at sound_path to the file at output_path"""
    if sound_path is None:
        raise ValueError("WavSteg recovery requires an input sound file path")
    if output_path is None:
        raise ValueError("WavSteg recovery requires an output file path")
    if bytes_to_recover is None:
        raise ValueError("WavSteg recovery requires the number of bytes to recover")

    start = time()
    with wave.open(sound_path, "r") as sound:
        # num_channels = sound.getnchannels()
        sample_width = sound.getsampwidth()
        num_frames = sound.getnframes()
        sound_frames = sound.readframes(num_frames)
        log.debug(f"{'Files read':<30} in {time() - start:.2f}s")

        if sample_width < 1 or sample_width > 4:
            # WavSteg doesn't support higher sample widths, see setsampwidth() in cpython/Libwave.py
            raise ValueError("File has an unsupported bit-depth")

        start = time()
        data = lsb_deinterleave_bytes(sound_frames, 8 * bytes_to_recover, num_lsb, byte_depth=sample_width)
        log.debug(f"{f'Recovered {bytes_to_recover} bytes':<30} in {time() - start:.2f}s")

        start = time()
        with open(output_path, "wb+") as output_file:
            output_file.write(bytes(data))
        log.debug(f"{'Written output file':<30} in {time() - start:.2f}s")
