#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

requirements = [
    # TODO: remove Click restriction after release of 8.1.6 or merge of
    #  https://github.com/pallets/click/pull/2565
    "Click<8.1.4", "Pillow", "numpy; python_version>='3.9'",
    "numpy>=1.15.4,<1.25.0; python_version>='3.8' and python_version<'3.9'"
]

setup(
    author="Ryan Gibson",
    author_email="ryanalexandergibson@gmail.com",
    name="stego-lsb",
    version="1.4.4",
    description="stego lsb",
    keywords="stego lsb",
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
