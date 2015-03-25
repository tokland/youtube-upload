#!/usr/bin/python2
#
# Author: Arnau Sanchez <pyarnau@gmail.com>
# Project site: https://github.com/tokland/youtube-upload
"""
Upload a video to Youtube from the command-line.

    $ youtube-upload --title="A.S. Mutter playing" \
                     --description="Anne Sophie Mutter plays Beethoven" \
                     --category=Music \
                     --tags="mutter, beethoven" \
                     anne_sophie_mutter.flv
    www.youtube.com/watch?v=pxzZ-fYjeYs
"""

import os
import sys
import optparse
import collections

import youtube_upload.auth
import youtube_upload.upload_video
import youtube_upload.categories
import youtube_upload.lib as lib

# http://code.google.com/p/python-progressbar (>= 2.3)
try:
    import progressbar
except ImportError:
    progressbar = None

class InvalidCategory(Exception): pass
class OptionsMissing(Exception): pass

EXIT_CODES = {
    OptionsMissing: 2,
    InvalidCategory: 3,
}

WATCH_VIDEO_URL = "https://www.youtube.com/watch?v={id}"

debug = lib.debug

def get_progress_info():
    """Return a function callback to update the progressbar."""
    build = collections.namedtuple("ProgressInfo", ["callback", "finish"])

    if progressbar:
        widgets = [
            progressbar.Percentage(), ' ',
            progressbar.Bar(), ' ',
            progressbar.ETA(), ' ',
            progressbar.FileTransferSpeed(),
        ]
        bar = progressbar.ProgressBar(widgets=widgets)
        def _callback(total_size, completed):
            if not hasattr(bar, "next_update"):
                bar.maxval = total_size
                bar.start()
            bar.update(completed)
        return build(callback=_callback, finish=bar.finish)
    else:
        return build(callback=None, finish=lambda: True)

def get_category_id(category):
    """Return category ID from its name."""
    if category:
        if category in youtube_upload.categories.IDS:
            return str(youtube_upload.categories.IDS[category])
        else:
            msg = "{0} is not a valid category".format(category)
            raise InvalidCategory(msg)

def upload_video(youtube, options, video_path, total_videos, index):
    """Upload video with index (for split videos)."""
    title = lib.to_utf8(options.title)
    description = lib.to_utf8(options.description or "").decode("string-escape")
    ns = dict(title=title, n=index+1, total=total_videos)
    complete_title = \
        (options.title_template.format(**ns) if total_videos > 1 else title)
    progress = get_progress_info()
    category_id = get_category_id(options.category)
    body = {
        "snippet": {
            "title": complete_title,
            "tags": map(str.strip, (options.tags or "").split(",")),
            "description": description,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": options.privacy
        },
        "recordingDetails": {
            "location": lib.string_to_dict(options.location),
        },
    }

    debug("Start upload: {0} ({1})".format(video_path, complete_title))
    video_id = youtube_upload.upload_video.upload(youtube, video_path, body,
        progress_callback=progress.callback, chunksize=16*1024)
    progress.finish()
    return video_id

def run_main(parser, options, args, output=sys.stdout):
    """Run the main scripts from the parsed options/args."""
    required_options = ["title"]
    missing = [opt for opt in required_options if not getattr(options, opt)]
    if missing:
        parser.print_usage()
        msg = "Some required option are missing: %s" % ", ".join(missing)
        raise OptionsMissing(msg)

    default_client_secrets = \
        os.path.join(sys.prefix, "share/youtube_upload/client_secrets.json")
    home = os.path.expanduser("~")
    default_credentials = os.path.join(home, ".youtube-upload-credentials.json")
    client_secrets = options.client_secrets or default_client_secrets
    credentials = options.credentials_file or default_credentials
    debug("Using client secrets: {0}".format(client_secrets))
    debug("Using credentials file: {0}".format(credentials))
    youtube = youtube_upload.auth.get_resource(client_secrets, credentials)

    for index, video_path in enumerate(args):
        video_id = upload_video(youtube, options, video_path, len(args), index)
        video_url = WATCH_VIDEO_URL.format(id=video_id)
        debug("Video URL: {0}".format(video_url))
        output.write(video_id + "\n")

def main(arguments):
    """Upload videos to Youtube."""
    usage = """Usage: %prog [OPTIONS] VIDEO_PATH [VIDEO_PATH2 ...]

    Upload videos to youtube."""
    parser = optparse.OptionParser(usage)

    # Video metadata
    parser.add_option('-t', '--title', dest='title', type="string",
        help='Video(s) title')
    parser.add_option('-c', '--category', dest='category', type="string",
        help='Video(s) category')
    parser.add_option('-d', '--description', dest='description', type="string",
        help='Video(s) description')
    parser.add_option('', '--tags', dest='tags', type="string",
        help='Video(s) tags (separated by commas: tag1,tag2,...)')
    parser.add_option('', '--privacy', dest='privacy', metavar="STRING",
        default="public", help='Privacy status (public | unlisted | private)')
    parser.add_option('', '--location', dest='location', type="string",
        default=None, metavar="latitude=VAL,longitude=VAL[,altitude=VAL]",
        help='Video(s) location"')
    parser.add_option('', '--title-template', dest='title_template',
        type="string", default="{title} [{n}/{total}]", metavar="STRING",
        help='Template for multiple videos (default: {title} [{n}/{total}])')

    # Authentication
    parser.add_option('', '--client-secrets', dest='client_secrets',
        type="string", help='Client secrets JSON file')
    parser.add_option('', '--credentials-file', dest='credentials_file',
        type="string", help='Client secrets JSON file')

    options, args = parser.parse_args(arguments)
    run_main(parser, options, args)

if __name__ == '__main__':
    sys.exit(lib.catch_exceptions(EXIT_CODES, main, sys.argv[1:]))
