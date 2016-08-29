#!/usr/bin/env python
# 
# Upload videos to Youtube from the command-line using APIv3.
#
# Author: Arnau Sanchez <pyarnau@gmail.com>
# Project: https://github.com/tokland/youtube-upload
"""
Upload a video to Youtube from the command-line.

    $ youtube-upload --title="A.S. Mutter playing" \
                     --description="Anne Sophie Mutter plays Beethoven" \
                     --category=Music \
                     --tags="mutter, beethoven" \
                     anne_sophie_mutter.flv
    pxzZ-fYjeYs
"""

import sys
import argparse

import googleapiclient.errors
import oauth2client

from . import upload
from . import lib

class OptionsError(Exception): pass

EXIT_CODES = {
    OptionsError: 2,
    upload.InvalidCategory: 3,
    upload.RequestError: 3,
    upload.AuthenticationError: 4,
    oauth2client.client.FlowExchangeError: 4,
    NotImplementedError: 5,
}

WATCH_VIDEO_URL = "https://www.youtube.com/watch?v={id}"

def cli(arguments):
    """Upload videos to Youtube."""
    usage = """Usage: %prog [OPTIONS] VIDEO

    Upload videos to Youtube."""
    parser = argparse.ArgumentParser(usage)

    # Video metadata
    parser.add_argument('-t', '--title', dest='title', type=str,
        help='Video title')
    parser.add_argument('-c', '--category', dest='category', type=str,
        help='Video category')
    parser.add_argument('-d', '--description', dest='description', type=str,
        help='Video description')
    parser.add_argument('--tags', dest='tags', type=str,
        help='Video tags (separated by commas: "tag1, tag2,...")')
    parser.add_argument('--privacy', dest='privacy', metavar="STRING",
        default="public", help='Privacy status (public | unlisted | private)')
    parser.add_argument('--publish-at', dest='publish_at', metavar="datetime",
       default=None, help='Publish date (ISO 8601): YYYY-MM-DDThh:mm:ss.sZ')
    parser.add_argument('--location', dest='location', type=str,
        default=None, metavar="latitude=VAL,longitude=VAL[,altitude=VAL]",
        help='Video location"')
    parser.add_argument('--recording-date', dest='recording_date', metavar="datetime",
        default=None, help="Recording date (ISO 8601): YYYY-MM-DDThh:mm:ss.sZ")
    parser.add_argument('--default-language', dest='default_language', type=str,
        default=None, metavar="string", 
        help="Default language (ISO 639-1: en | fr | de | ...)")
    parser.add_argument('--default-audio-language', dest='default_audio_language', type=str,
        default=None, metavar="string", 
        help="Default audio language (ISO 639-1: en | fr | de | ...)")
    parser.add_argument('--thumbnail', dest='thumb', type=str, metavar="FILE", 
        help='Image file to use as video thumbnail (JPEG or PNG)')
    parser.add_argument('--playlist', dest='playlist', type=str,
        help='Playlist title (if it does not exist, it will be created)')

    # Authentication
    parser.add_argument('--client-secrets', dest='client_secrets',
        type=str, help='Client secrets JSON path file')
    parser.add_argument('--credentials-file', dest='credentials_file',
        type=str, help='Credentials JSON path file')
    parser.add_argument('--auth-browser', dest='auth_browser', action='store_true',
        help='Open a GUI browser to authenticate if required')

    #Additional options
    parser.add_argument('--open-link', dest='open_link', action='store_true',
        help='Opens video URL in a web browser')

    # Positional arguments
    parser.add_argument('video_path', metavar="VIDEO PATH", type=str,
        help="Video to upload (local path)")
  
    options = parser.parse_args(arguments)
    resource = upload.get_resource(options)
    video_id = upload.upload_video(resource, options.video_path, options)
    video_url = WATCH_VIDEO_URL.format(id=video_id)
    lib.debug("Video URL: {0}".format(video_url))
    sys.stdout.write(video_id + "\n")

def run():
    sys.exit(lib.catch_exceptions(EXIT_CODES, cli, sys.argv[1:]))
  
if __name__ == '__main__':
    run()
