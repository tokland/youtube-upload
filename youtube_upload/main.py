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

import os
import sys
import optparse
import collections

import apiclient.errors
import oauth2client

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
class AuthenticationError(Exception): pass
class RequestError(Exception): pass

EXIT_CODES = {
    OptionsMissing: 2,
    InvalidCategory: 3,
    RequestError: 3,
    AuthenticationError: 4,
    oauth2client.client.FlowExchangeError: 4,
    NotImplementedError: 5,
}

WATCH_VIDEO_URL = "https://www.youtube.com/watch?v={id}"

debug = lib.debug

def get_progress_info():
    """Return a function callback to update the progressbar."""
    progressinfo = collections.namedtuple("ProgressInfo", ["callback", "finish"])

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
        def _finish():
            if hasattr(bar, "next_update"):
                return bar.finish()
        return progressinfo(callback=_callback, finish=_finish)
    else:
        return progressinfo(callback=None, finish=lambda: True)

def get_category_id(category):
    """Return category ID from its name."""
    if category:
        if category in youtube_upload.categories.IDS:
            ncategory = youtube_upload.categories.IDS[category]
            debug("Using category: {0} (id={1})".format(category, ncategory))
            return str(youtube_upload.categories.IDS[category])
        else:
            msg = "{0} is not a valid category".format(category)
            raise InvalidCategory(msg)

def upload_video(youtube, options, video_path, total_videos, index):
    """Upload video with index (for split videos)."""
    u = lib.to_utf8
    title = u(options.title)
    description = u(options.description or "").decode("string-escape")
    tags = [u(s.strip()) for s in (options.tags or "").split(",")]
    ns = dict(title=u(options.title), n=index+1, total=total_videos)
    complete_title = \
        (options.title_template.format(**ns) if total_videos > 1 else title)
    progress = get_progress_info()
    category_id = get_category_id(options.category)
    request_body = {
        "snippet": {
            "title": complete_title,
            "description": description,
            "categoryId": category_id,
            "tags": tags,
        },
        "status": {
            "privacyStatus": options.privacy,
        },
        "recordingDetails": {
            "location": lib.string_to_dict(options.location),
        },
    }

    debug("Start upload: {0}".format(video_path))
    try:
        video_id = youtube_upload.upload_video.upload(youtube, video_path, 
            request_body, progress_callback=progress.callback)
    except apiclient.errors.HttpError, error:
        raise RequestError("Server response was: {0}".format(error.content.strip()))
    progress.finish()
    return video_id

def run_main(parser, options, args, output=sys.stdout):
    """Run the main scripts from the parsed options/args."""
    required_options = ["title"]
    missing = [opt for opt in required_options if not getattr(options, opt)]
    if missing:
        parser.print_usage()
        msg = "Some required option are missing: {0}".format(", ".join(missing))
        raise OptionsMissing(msg)
    home = os.path.expanduser("~")
    default_client_secrets = lib.get_first_existing_filename(
        [sys.prefix, os.path.join(sys.prefix, "local")],
        "share/youtube_upload/client_secrets.json")  
    default_credentials = os.path.join(home, ".youtube-upload-credentials.json")
    client_secrets = options.client_secrets or default_client_secrets or \
        os.path.join(home, ".client_secrets.json")
    credentials = options.credentials_file or default_credentials
    debug("Using client secrets: {0}".format(client_secrets))
    debug("Using credentials file: {0}".format(credentials))
    get_code_callback = (youtube_upload.auth.browser.get_code 
        if options.auth_browser else youtube_upload.auth.console.get_code)
    youtube = youtube_upload.auth.get_resource(client_secrets, credentials,
        get_code_callback=get_code_callback)

    if youtube:
        for index, video_path in enumerate(args):
            video_id = upload_video(youtube, options, video_path, len(args), index)
            video_url = WATCH_VIDEO_URL.format(id=video_id)

            if options.thumb:
                youtube.thumbnails().set(videoId=video_id, media_body=options.thumb).execute()

            if options.playlist:
                # find playlist with given name
                existing_playlist_id = None
                playlists = youtube.playlists()
                request = playlists.list(mine=True, part='id,snippet')
                while request is not None:
                    results = request.execute()
                    for item in results['items']:
                        if item.get('snippet', {}).get('title') == options.playlist:
                            existing_playlist_id = item.get('id')

                    # stop paginating playlists on first matching playlist title
                    if existing_playlist_id is None:
                        request = playlists.list_next(request, results)
                    else:
                        break

                # create playlist, if necessary
                if existing_playlist_id is None:
                    playlists_insert_response = youtube.playlists().insert(part="snippet,status", body={
                        "snippet": {
                            "title": options.playlist
                        },
                        "status": {
                            "privacyStatus": options.privacy
                        }
                    }).execute()
                    existing_playlist_id = playlists_insert_response.get('id', None)

                # something has gone wrong
                if existing_playlist_id is None:
                    debug('Error creating playlist')
                    sys.exit(1)

                # add video to playlist
                youtube.playlistItems().insert(part='snippet', body={
                    "snippet": {
                        "playlistId": existing_playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }).execute()
                debug("Added video to playlist '{0}'".format(options.playlist))

            debug("Video URL: {0}".format(video_url))
            output.write(video_id + "\n")
    else:
        raise AuthenticationError("Cannot get youtube resource")

def main(arguments):
    """Upload videos to Youtube."""
    usage = """Usage: %prog [OPTIONS] VIDEO [VIDEO2 ...]

    Upload videos to Youtube."""
    parser = optparse.OptionParser(usage)

    # Video metadata
    parser.add_option('-t', '--title', dest='title', type="string",
        help='Video title')
    parser.add_option('-c', '--category', dest='category', type="string",
        help='Video category')
    parser.add_option('-d', '--description', dest='description', type="string",
        help='Video description')
    parser.add_option('', '--tags', dest='tags', type="string",
        help='Video tags (separated by commas: "tag1, tag2,...")')
    parser.add_option('', '--privacy', dest='privacy', metavar="STRING",
        default="public", help='Privacy status (public | unlisted | private)')
    parser.add_option('', '--location', dest='location', type="string",
        default=None, metavar="latitude=VAL,longitude=VAL[,altitude=VAL]",
        help='Video location"')
    parser.add_option('', '--thumbnail', dest='thumb', type="string",
        help='Video thumbnail')
    parser.add_option('', '--playlist', dest='playlist', type="string",
        help='Playlist title (will create if necessary)')
    parser.add_option('', '--title-template', dest='title_template',
        type="string", default="{title} [{n}/{total}]", metavar="STRING",
        help='Template for multiple videos (default: {title} [{n}/{total}])')

    # Authentication
    parser.add_option('', '--client-secrets', dest='client_secrets',
        type="string", help='Client secrets JSON file')
    parser.add_option('', '--credentials-file', dest='credentials_file',
        type="string", help='Credentials JSON file')
    parser.add_option('', '--auth-browser', dest='auth_browser', action="store_true",
        help='Open a GUI browser to authenticate if required')

    options, args = parser.parse_args(arguments)
    run_main(parser, options, args)

if __name__ == '__main__':
    sys.exit(lib.catch_exceptions(EXIT_CODES, main, sys.argv[1:]))
