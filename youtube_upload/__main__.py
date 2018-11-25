#!/usr/bin/env python
from __future__ import unicode_literals

# Execute with
# $ python youtube_upload/__main__.py (2.6+)
# $ python -m youtube_upload          (2.7+)

import sys

if __package__ is None and not hasattr(sys, 'frozen'):
    # direct call of __main__.py
    import os.path
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

import youtube_upload.main

if __name__ == '__main__':
    youtube_upload.main.main(sys.argv[1:])
