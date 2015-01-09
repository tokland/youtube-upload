#!/usr/bin/python
"""Upload videos to Youtube."""
from youtube_upload import VERSION
from distutils.core import setup

setup_kwargs = {
    "name": "youtube-upload",
    "version": VERSION,
    "description": "Upload videos to Youtube",
    "author": "Arnau Sanchez",
    "author_email": "tokland@gmail.com",
    "url": "http://code.google.com/p/youtube-upload/",
    "packages": ["youtube_upload/"],
    "scripts": ["bin/youtube-upload"],
    "license": "GNU Public License v3.0",
    "long_description": " ".join(__doc__.strip().splitlines()),
    "classifiers": [
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
}

setup(**setup_kwargs)
