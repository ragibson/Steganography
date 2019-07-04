# -*- coding: utf-8 -*-
"""
    stego_lsb.cli
    ~~~~~~~~~~~~~

    This module provides the command line interface for:
        - hiding and recovering data in .wav files
        - hiding and recovering data in bitmap (.bmp and .png)
          files
        - detecting images which have modified using the
          LSB methods.

    :copyright: (c) 2015 by Ryan Gibson, see AUTHORS.md for more details.
    :license: MIT License, see LICENSE.md for more details.
"""
import logging

import click

from stego_lsb import LSBSteg, StegDetect, WavSteg, bit_manipulation

# enable logging output
logging.basicConfig(format="%(message)s", level=logging.INFO)
log = logging.getLogger("stego_lsb")
log.setLevel(logging.DEBUG)


@click.group()
@click.version_option()
def main(args=None):
    """Console script for stegolsb."""


@main.command(context_settings=dict(max_content_width=120))
@click.option("--hide", "-h", is_flag=True, help="To hide data in an image file")
@click.option(
    "--recover", "-r", is_flag=True, help="To recover data from an image file"
)
@click.option(
    "--analyze",
    "-a",
    is_flag=True,
    default=False,
    show_default=True,
    help="Print how much data can be hidden within an image",
)
@click.option(
    "--input", "-i", "input_fp", help="Path to an bitmap (.bmp or .png) image"
)
@click.option("--secret", "-s", "secret_fp", help="Path to a file to hide in the image")
@click.option("--output", "-o", "output_fp", help="Path to an output file")
@click.option(
    "--lsb-count",
    "-n",
    default=2,
    show_default=True,
    help="How many LSBs to use",
    type=int,
)
@click.option(
    "--compression",
    "-c",
    help="1 (best speed) to 9 (smallest file size)",
    default=1,
    show_default=True,
    type=click.IntRange(1, 9),
)
@click.pass_context
def steglsb(
    ctx, hide, recover, analyze, input_fp, secret_fp, output_fp, lsb_count, compression
):
    """Hides or recovers data in and from an image"""
    try:
        if analyze:
            LSBSteg.analysis(input_fp, secret_fp, lsb_count)

        if hide:
            LSBSteg.hide_data(input_fp, secret_fp, output_fp, lsb_count, compression)
        elif recover:
            LSBSteg.recover_data(input_fp, output_fp, lsb_count)

        if not hide and not recover and not analyze:
            click.echo(ctx.get_help())
    except ValueError as e:
        log.debug(e)
        click.echo(ctx.get_help())


@main.command()
@click.option("--input", "-i", "image_path", help="Path to an image")
@click.option(
    "--lsb-count",
    "-n",
    default=2,
    show_default=2,
    type=int,
    help="How many LSBs to display",
)
@click.pass_context
def stegdetect(ctx, image_path, lsb_count):
    """Shows the n least significant bits of image"""
    if image_path:
        StegDetect.show_lsb(image_path, lsb_count)
    else:
        click.echo(ctx.get_help())


@main.command()
@click.option("--hide", "-h", is_flag=True, help="To hide data in a sound file")
@click.option("--recover", "-r", is_flag=True, help="To recover data from a sound file")
@click.option("--input", "-i", "input_fp", help="Path to a .wav file")
@click.option(
    "--secret", "-s", "secret_fp", help="Path to a file to hide in the sound file"
)
@click.option("--output", "-o", "output_fp", help="Path to an output file")
@click.option(
    "--lsb-count",
    "-n",
    default=2,
    show_default=True,
    help="How many LSBs to use",
    type=int,
)
@click.option(
    "--bytes",
    "-b",
    "num_bytes",
    help="How many bytes to recover from the sound file",
    type=int,
)
@click.pass_context
def wavsteg(ctx, hide, recover, input_fp, secret_fp, output_fp, lsb_count, num_bytes):
    """Hides or recovers data in and from a sound file"""
    try:
        if hide:
            WavSteg.hide_data(input_fp, secret_fp, output_fp, lsb_count)
        elif recover:
            WavSteg.recover_data(input_fp, output_fp, lsb_count, num_bytes)
        else:
            click.echo(ctx.get_help())
    except ValueError as e:
        log.debug(e)
        click.echo(ctx.get_help())


@main.command()
def test():
    """Runs a performance test and verifies decoding consistency"""
    bit_manipulation.test()
