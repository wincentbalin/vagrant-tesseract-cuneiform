#!/usr/bin/env python3
"""Rewrap lines without breaking words"""

import sys
import argparse
import textwrap


argparser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)
argparser.add_argument('infile', type=argparse.FileType('r', encoding='UTF-8'))
argparser.add_argument('outfile', type=argparse.FileType('w', encoding='UTF-8'))
argparser.add_argument('width', type=int)
args = argparser.parse_args()

for line in args.infile:
    for wrapped in textwrap.wrap(line, args.width):
        args.outfile.write('{}\n'.format(wrapped))

