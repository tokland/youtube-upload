#!/usr/bin/python2
#
# Youtube-upload is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Youtube-upload is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Youtube-upload. If not, see <http://www.gnu.org/licenses/>.
#
# Author: Arnau Sanchez <pyarnau@gmail.com>
# Site: https://github.com/tokland/youtube-upload
"""
Upload a video to Youtube from the command-line.

    $ youtube-upload --title="A.S. Mutter playing" \
                     --description="Anne Sophie Mutter plays Beethoven" \
                     --category=Music \
                     --keywords="mutter, beethoven" \
                     anne_sophie_mutter.flv
    www.youtube.com/watch?v=pxzZ-fYjeYs
"""

import os
import sys
import locale
import optparse
import collections

import youtube_upload.auth
import youtube_upload.upload_video
import youtube_upload.categories

# http://code.google.com/p/python-progressbar (>= 2.3)
try:
    import progressbar
except ImportError:
    progressbar = None

class InvalidCategory(Exception): pass
class VideoArgumentMissing(Exception): pass
class OptionsMissing(Exception): pass
class BadAuthentication(Exception): pass
class ParseError(Exception): pass
class VideoNotFound(Exception): pass
class UnsuccessfulHTTPResponseCode(Exception): pass

VERSION = "0.8.0"

EXIT_CODES = {
    # Non-retryable
    BadAuthentication: 1,
    VideoArgumentMissing: 2,
    OptionsMissing: 2,
    InvalidCategory: 3,
    ParseError: 5,
    VideoNotFound: 6,
    # Retryable
    UnsuccessfulHTTPResponseCode: 100,
}

WATCH_VIDEO_URL = "https://www.youtube.com/watch?v={id}"

ProgressInfo = collections.namedtuple("ProgressInfo", ["callback", "finish"])

def to_utf8(s):
    """Re-encode string from the default system encoding to UTF-8."""
    current = locale.getpreferredencoding()
    return s.decode(current).encode("UTF-8") if s and current != "UTF-8" else s

def debug(obj, fd=sys.stderr):
    """Write obj to standard error."""
    string = str(obj.encode(get_encoding(fd), "backslashreplace")
                 if isinstance(obj, unicode) else obj)
    fd.write(string + "\n")

def catch_exceptions(exit_codes, fun, *args, **kwargs):
    """
    Catch exceptions on fun(*args, **kwargs) and return the exit code specified
    in the exit_codes dictionary. Return 0 if no exception is raised.
    """
    try:
        fun(*args, **kwargs)
        return 0
    except tuple(exit_codes.keys()) as exc:
        debug("[%s] %s" % (exc.__class__.__name__, exc))
        return exit_codes[exc.__class__]

def get_encoding(fd):
    """Guess terminal encoding."""
    return fd.encoding or locale.getpreferredencoding()

def compact(it):
    """Filter false (in the truth sense) elements in iterator."""
    return filter(bool, it)

def tosize(seq, size):
    """Return list of fixed length from sequence."""
    return seq[:size] if len(seq) >= size else (seq + [None] * (size-len(seq)))

def first(it):
    """Return first element in iterable."""
    return it.next()

def get_progress_info():
    """Return a function callback to update the progressbar."""
    def _callback(total_size, completed):
        if not hasattr(bar, "next_update"):
            bar.maxval = total_size
            bar.start()
        bar.update(completed)

    widgets = [
        progressbar.Percentage(), ' ',
        progressbar.Bar(), ' ',
        progressbar.ETA(), ' ',
        progressbar.FileTransferSpeed(),
    ]
    bar = progressbar.ProgressBar(widgets=widgets)
    return ProgressInfo(callback=_callback, finish=bar.finish)

def string_to_dict(string):
    """Return dictionary from string "key1=value1, key2=value2"."""
    pairs = [s.strip() for s in (string or "").split(",")]
    return dict(pair.split("=") for pair in pairs)

def upload_video(youtube, options, video_path, total_videos, index):
    """Upload video with index (for split videos)."""
    title = to_utf8(options.title)
    description = to_utf8(options.description or "").decode("string-escape")
    ns = dict(title=title, n=index+1, total=total_videos)
    complete_title = \
        (options.title_template.format(**ns) if total_videos > 1 else title)
    progress = get_progress_info()
    if options.category:
        ids = youtube_upload.categories.IDS
        if options.category in ids:
            category_id = str(ids[options.category])
        else:
            msg = "{} is not a valid category".format(options.category)
            raise InvalidCategory(msg)
    else:
        category_id = None

    body = {
        "snippet": {
            "title": complete_title,
            "tags": map(str.strip, (options.keywords or "").split(",")),
            "description": description,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": options.privacy
        },
        "recordingDetails": {
            "location": string_to_dict(options.location),
        },
    }

    debug("Start upload: {} ({})".format(video_path, complete_title))
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
    default_credentials = os.path.join(home, ".youtube_upload-credentials.json")
    client_secrets = options.client_secrets or default_client_secrets
    credentials = options.credentials_file or default_credentials
    debug("Using client secrets: {}".format(client_secrets))
    debug("Using credentials file: {}".format(credentials))
    youtube = youtube_upload.auth.get_resource(client_secrets, credentials)

    for index, video_path in enumerate(args):
        video_id = upload_video(youtube, options, video_path, len(args), index)
        video_url = WATCH_VIDEO_URL.format(id=video_id)
        debug("Watch URL: {}".format(video_url))
        output.write(video_id + "\n")

def main(arguments):
    """Upload video to Youtube."""
    usage = """Usage: %prog [OPTIONS] VIDEO_PATH [VIDEO_PATH2 ...]

    Upload videos to youtube."""
    parser = optparse.OptionParser(usage, version=VERSION)

    # Required options
    parser.add_option('-t', '--title', dest='title', type="string",
        help='Video(s) title')
    parser.add_option('-c', '--category', dest='category', type="string",
        help='Video(s) category')

    # Optional options
    parser.add_option('-d', '--description', dest='description', type="string",
        help='Video(s) description')
    parser.add_option('', '--keywords', dest='keywords', type="string",
        help='Video(s) keywords (separated by commas: tag1,tag2,...)')
    parser.add_option('', '--title-template', dest='title_template',
        type="string", default="{title} [{n}/{total}]", metavar="STRING",
        help='Template for multiple videos (default: {title} [{n}/{total}])')
    parser.add_option('', '--privacy', dest='privacy', metavar="STRING",
        default="public", help='Privacy status (public | unlisted | private)')
    parser.add_option('', '--location', dest='location', type="string",
        default=None, metavar="latitude=VAL, longitude=VAL, altitude=VAL",
        help='Video(s) location"')

    # Authentication
    parser.add_option('', '--client-secrets', dest='client_secrets',
        type="string", help='Client secrets JSON file')
    parser.add_option('', '--credentials-file', dest='credentials_file',
        type="string", help='Client secrets JSON file')

    options, args = parser.parse_args(arguments)
    run_main(parser, options, args)

if __name__ == '__main__':
    sys.exit(catch_exceptions(EXIT_CODES, main, sys.argv[1:]))
