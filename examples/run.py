#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import quickavro

import example1
import example2
import example3
import example4
import example5
import example6
import example7


if __name__ == '__main__':
    sys.stdout.write("Running example1 - read/write 1 block ...\n")
    example1.main()
    sys.stdout.write("\n")
    sys.stdout.write("Running example2 - read/write 1 block (alt) ...\n")
    example2.main()
    sys.stdout.write("\n")
    sys.stdout.write("Running example3 - read/write 1,000,000 records ...\n")
    example3.main()
    sys.stdout.write("\n")
    sys.stdout.write("Running example4 - read/write 1 block w/ deflate ...\n")
    example4.main()
    sys.stdout.write("\n")
    sys.stdout.write("Running example5 - read/write 1 block w/ snappy ...\n")
    example5.main()
    sys.stdout.write("\n")
    sys.stdout.write("Running example6 - read/write 1 block w/ encoder ...\n")
    example6.main()
    sys.stdout.write("\n")
    sys.stdout.write("Running example7 - read/write 1,000,000 records w/ encoder ...\n")
    example7.main()
