# The MIT License (MIT)
#
# Copyright (c) 2018 Ryan Gibson
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

import os
from math import ceil
from time import time

import numpy as np

byte_depth_to_dtype = {1: np.uint8, 2: np.uint16, 4: np.uint32, 8: np.uint64}


def roundup(x, base=1):
    return int(ceil(x / base)) * base


def lsb_interleave_bytes(carrier, payload, num_lsb, truncate=False, byte_depth=1):
    """
    Interleave the bytes of payload into the num_lsb LSBs of carrier.

    :param carrier: carrier bytes
    :param payload: payload bytes
    :param num_lsb: number of least significant bits to use
    :param truncate: if True, will only return the interleaved part
    :param byte_depth: byte depth of carrier values
    :return: The interleaved bytes
    """

    plen = len(payload)
    payload_bits = np.zeros(shape=(roundup(plen, num_lsb), 8), dtype=np.uint8)
    payload_bits[:plen, :] = np.unpackbits(
        np.frombuffer(payload, dtype=np.uint8, count=plen)
    ).reshape(plen, 8)

    bit_height = roundup(np.size(payload_bits) / num_lsb)
    carrier_dtype = byte_depth_to_dtype[byte_depth]
    carrier_bits = np.unpackbits(
        np.frombuffer(carrier, dtype=carrier_dtype, count=bit_height).view(np.uint8)
    ).reshape(bit_height, 8 * byte_depth)

    carrier_bits[:, 8 - num_lsb : 8] = payload_bits.reshape(bit_height, num_lsb)

    ret = np.packbits(carrier_bits).tobytes()
    return ret if truncate else ret + carrier[bit_height:]


def lsb_deinterleave_bytes(carrier, num_bits, num_lsb, byte_depth=1):
    """
    Deinterleave num_bits bits from the num_lsb LSBs of carrier.

    :param carrier: carrier bytes
    :param num_bits: number of num_bits to retrieve
    :param num_lsb: number of least significant bits to use
    :param byte_depth: byte depth of carrier values
    :return: The deinterleaved bytes
    """

    plen = roundup(num_bits / num_lsb)
    carrier_dtype = byte_depth_to_dtype[byte_depth]
    payload_bits = np.unpackbits(
        np.frombuffer(carrier, dtype=carrier_dtype, count=plen).view(np.uint8)
    ).reshape(plen, 8 * byte_depth)[:, 8 - num_lsb : 8]
    return np.packbits(payload_bits).tobytes()[: num_bits // 8]


def lsb_interleave_list(carrier, payload, num_lsb):
    """Runs lsb_interleave_bytes with a List[uint8] carrier.

    This is slower than working with bytes directly, but is often
    unavoidable if working with libraries that require using lists."""

    bit_height = roundup(8 * roundup(len(payload), num_lsb) / num_lsb)
    carrier_bytes = np.array(carrier[:bit_height], dtype=np.uint8).tobytes()
    interleaved = lsb_interleave_bytes(carrier_bytes, payload, num_lsb, truncate=True)
    carrier[:bit_height] = np.frombuffer(interleaved, dtype=np.uint8).tolist()
    return carrier


def lsb_deinterleave_list(carrier, num_bits, num_lsb):
    """Runs lsb_deinterleave_bytes with a List[uint8] carrier.

    This is slower than working with bytes directly, but is often
    unavoidable if working with libraries that require using lists."""

    plen = roundup(num_bits / num_lsb)
    carrier_bytes = np.array(carrier[:plen], dtype=np.uint8).tobytes()
    deinterleaved = lsb_deinterleave_bytes(carrier_bytes, num_bits, num_lsb)
    return deinterleaved


def test(carrier_len=10 ** 7, payload_len=10 ** 6):
    """Runs consistency tests with a random carrier and payload of byte
    lengths carrier_len and payload_len, respectively."""

    def print_results(e_rates, d_rates):
        print("\n" + "-" * 40)
        row_fmt = "| {:<7}| {:<13}| {:<13}|"
        print(row_fmt.format("# LSBs", "Encode Rate", "Decode rate"))
        for n, e, d in zip(range(1, 9), e_rates[1:], d_rates[1:]):
            print(row_fmt.format(n, e, d))
        print("-" * 40)

    current_progress = 0

    def progress():
        nonlocal current_progress
        print(
            "\rProgress: ["
            + "#" * current_progress
            + "-" * (32 - current_progress)
            + "]",
            end="",
            flush=True,
        )
        current_progress += 1

    print(
        "Testing {:.1f} MB payload -> {:.1f} MB carrier...".format(
            payload_len / 1e6, carrier_len / 1e6
        )
    )
    progress()

    carrier = os.urandom(carrier_len)
    payload = os.urandom(payload_len)
    encode_rates = [""] * 9
    decode_rates = [""] * 9

    for num_lsb in range(1, 9):
        # LSB interleavings that match carrier length
        encoded = lsb_interleave_bytes(carrier, payload, num_lsb)
        progress()
        decoded = lsb_deinterleave_bytes(encoded, 8 * payload_len, num_lsb)
        progress()

        # truncated LSB interleavings
        encode_time = time()
        truncated_encode = lsb_interleave_bytes(
            carrier, payload, num_lsb, truncate=True
        )
        encode_time = time() - encode_time
        progress()
        decode_time = time()
        truncated_decode = lsb_deinterleave_bytes(
            truncated_encode, 8 * payload_len, num_lsb
        )
        decode_time = time() - decode_time
        progress()

        encode_rates[num_lsb] = "{:<6.1f} MB/s".format(
            (payload_len / 1e6) / encode_time
        )
        decode_rates[num_lsb] = "{:<6.1f} MB/s".format(
            (payload_len / 1e6) / decode_time
        )

        if decoded != payload or truncated_decode != payload:
            print("\nTest failed at {} LSBs!".format(num_lsb))
            return False

    print_results(encode_rates, decode_rates)
    return True


if __name__ == "__main__":
    test()
