#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from .reader import FileReader


def main():
    if not len(sys.argv) > 1:
        sys.stderr.write("Missing arguments\n")
        sys.exit(0)
    try:
        with FileReader(sys.argv[1]) as reader:
            for record in reader.records():
                print(record)
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == '__main__':
    main()
