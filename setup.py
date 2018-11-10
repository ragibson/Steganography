#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

requirements = ["Pillow"]


setup(
    author="Ryan Gibson",
    author_email="ryanalexandergibson@gmail.com",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="stego lsb",
    install_requires=requirements,
    license="MIT",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="stego lsb",
    name="stego_lsb",
    packages=find_packages(include=["stego_lsb"]),
    url="https://git.someblocks.com/sh4nks/stego_lsb.git",
    version="0.1.0",
    zip_safe=False,
)
