from stego_lsb.bit_manipulation import lsb_interleave_bytes, lsb_deinterleave_bytes
import numpy as np
import unittest


class TestBitManipulation(unittest.TestCase):
    def assertConsistentInterleaving(self, carrier, payload, num_lsb, byte_depth=1):
        num_payload_bits = 8 * len(payload)

        encoded = lsb_interleave_bytes(carrier, payload, num_lsb, byte_depth=byte_depth)
        decoded = lsb_deinterleave_bytes(
            encoded, num_payload_bits, num_lsb, byte_depth=byte_depth
        )
        self.assertEqual(decoded, payload)  # payload correctly decoded
        self.assertEqual(
            len(encoded), len(carrier)
        )  # message length is unchanged after interleaving

        truncated_encode = lsb_interleave_bytes(
            carrier, payload, num_lsb, byte_depth=byte_depth, truncate=True
        )
        truncated_decode = lsb_deinterleave_bytes(
            truncated_encode, num_payload_bits, num_lsb, byte_depth=byte_depth
        )
        self.assertEqual(truncated_decode, payload)

    def check_random_interleaving(self, byte_depth=1, num_trials=256):
        np.random.seed(0)
        for _ in range(num_trials):
            carrier_len = np.random.randint(1, 16384)
            num_lsb = np.random.randint(1, 8 * byte_depth + 1)
            payload_len = carrier_len * num_lsb // (8 * byte_depth)
            carrier = np.random.randint(0, 256, size=carrier_len).tobytes()
            payload = np.random.randint(0, 256, size=payload_len).tobytes()
            self.assertConsistentInterleaving(
                carrier, payload, num_lsb, byte_depth=byte_depth
            )

    def test_interleaving_consistency_8bit(self):
        self.check_random_interleaving(byte_depth=1)

    def test_interleaving_consistency_16bit(self):
        self.check_random_interleaving(byte_depth=2)

    def test_interleaving_consistency_32bit(self):
        self.check_random_interleaving(byte_depth=4)

    def test_interleaving_consistency_64bit(self):
        self.check_random_interleaving(byte_depth=8)


if __name__ == "__main__":
    unittest.main()
