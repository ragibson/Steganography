#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

requirements = [
    "Click", "Pillow", "numpy; python_version>='3.9'",
    "numpy<1.25.0; python_version>='3.8' and python_version<'3.9'"
]

setup(
    author="Ryan Gibson",
    author_email="ryan.alex.gibson@gmail.com",
    name="stego-lsb",
    version="1.5.3",
    description="Least Significant Bit Steganography for bitmap images (.bmp "
                "and .png), WAV sound files, and byte sequences. Simple LSB "
                "Steganalysis (LSB extraction) for bitmap images.",
    keywords="steganography steganalysis",
    license="MIT",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/ragibson/Steganography",
    install_requires=requirements,
    entry_points="""
        [console_scripts]
        stegolsb=stego_lsb.cli:main
    """,
    package_data={"stego_lsb": ["py.typed"]},
    include_package_data=True,
    packages=find_packages(include=["stego_lsb"]),
    zip_safe=False,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
