#!/usr/bin/python
"""Upload videos to Youtube."""
from distutils.core import setup

setup_kwargs = {
    "name": "youtube-upload",
    "version": "0.8.0",
    "description": "Upload videos to Youtube",
    "author": "Arnau Sanchez",
    "author_email": "pyarnau@gmail.com",
    "url": "https://github.com/tokland/youtube-upload",
    "packages": ["youtube_upload/", "youtube_upload/auth"],
    "data_files": [("share/youtube_upload", ['client_secrets.json'])],
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
    "entry_points": {
        'console_scripts': [
            'youtube-upload = youtube_upload.main:run'
        ],
    },
    "install_requires":[
        'google-api-python-client',
        'progressbar2'
    ]
}

setup(**setup_kwargs)
