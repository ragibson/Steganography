from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from click.testing import Result

import os
import unittest
import wave

import numpy as np
from click.testing import CliRunner
from PIL import Image

from stego_lsb.cli import main

PAYLOAD = b"example payload"
FILES = ["input.png", "input.wav", "secret.txt", "steg.png", "steg.wav", "recovered.txt", "input_2LSBs.png"]


class TestCli(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

        with Image.fromarray(np.random.randint(0, 256, size=(8, 8, 3), dtype=np.uint8)) as image:
            image.save("input.png")

        with wave.open("input.wav", "w") as file:
            file.setnchannels(1)
            file.setsampwidth(1)
            file.setframerate(8000)
            file.writeframes(np.random.randint(0, 256, size=4096, dtype=np.uint8))

        with open("secret.txt", "wb") as file:
            file.write(PAYLOAD)

    def tearDown(self) -> None:
        for filename in FILES:
            if os.path.exists(filename):
                os.remove(filename)

    def invoke(self, *args: str) -> "Result":
        result = self.runner.invoke(main, list(args))
        self.assertEqual(result.exit_code, 0)  # just check it didn't fail
        return result

    def test_steglsb_commands(self) -> None:
        self.invoke("steglsb", "--hide", "-i", "input.png", "-s", "secret.txt", "-o", "steg.png", "-n", "2")
        self.invoke("steglsb", "--recover", "-i", "steg.png", "-o", "recovered.txt", "-n", "2")
        with open("recovered.txt", "rb") as file:
            self.assertEqual(file.read(), PAYLOAD)

    def test_wavsteg_commands(self) -> None:
        self.invoke("wavsteg", "--hide", "-i", "input.wav", "-s", "secret.txt", "-o", "steg.wav", "-n", "2")
        self.invoke("wavsteg", "--recover", "-i", "steg.wav", "-o", "recovered.txt", "-n", "2",
                    "-b", str(len(PAYLOAD)))
        with open("recovered.txt", "rb") as file:
            self.assertEqual(file.read(), PAYLOAD)

    def test_help_and_error_outputs(self) -> None:
        for args in [["steglsb"], ["steglsb", "--help"], ["wavsteg"], ["wavsteg", "--help"]]:
            self.assertIn("hides", self.invoke(*args).output.lower())

    def test_stegdetect(self) -> None:
        self.invoke("stegdetect", "-i", "input.png", "-n", "2")
        self.assertTrue(os.path.exists("input_2LSBs.png"))


if __name__ == "__main__":
    unittest.main()
