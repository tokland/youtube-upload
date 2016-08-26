import os
import sys
import collections
import webbrowser

import googleapiclient.errors
import oauth2client

from . import lib
from . import playlists
from . import auth
from . import upload_video
from . import categories

# http://code.google.com/p/python-progressbar (>= 2.3)
try:
    import progressbar
except ImportError:
    progressbar = None

debug = lib.debug
struct = collections.namedtuple

class InvalidCategory(Exception): pass
class AuthenticationError(Exception): pass
class RequestError(Exception): pass

def open_link(url):
    """Opens a URL link in the client's browser."""
    webbrowser.open(url)

def get_progress_info():
    """Return a function callback to update the progressbar."""
    progressinfo = struct("ProgressInfo", ["callback", "finish"])

    if progressbar:
        bar = progressbar.ProgressBar(widgets=[
            progressbar.Percentage(), ' ',
            progressbar.Bar(), ' ',
            progressbar.FileTransferSpeed(),
        ])
        def _callback(total_size, completed):
            if not hasattr(bar, "next_update"):
                if hasattr(bar, "maxval"):
                    bar.maxval = total_size
                else:
                    bar.max_value = total_size
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
        if category in categories.IDS:
            ncategory = categories.IDS[category]
            debug("Using category: {0} (id={1})".format(category, ncategory))
            return str(categories.IDS[category])
        else:
            msg = "{0} is not a valid category".format(category)
            raise InvalidCategory(msg)

def upload_youtube_video(youtube, options, video_path):
    """Upload video."""
    u = lib.to_utf8
    title = u(options.title)
    if hasattr(u('string'), 'decode'):   
        description = u(options.description or "").decode("string-escape")
    else:
        description = options.description
    if options.publish_at:    
      debug("Your video will remain private until specified date.")
      
    tags = [u(s.strip()) for s in (options.tags or "").split(",")]
    progress = get_progress_info()
    category_id = get_category_id(options.category)
    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": category_id,
            "tags": tags,
            "defaultLanguage": options.default_language,
            "defaultAudioLanguage": options.default_audio_language,

        },
        "status": {
            "privacyStatus": ("private" if options.publish_at else options.privacy),
            "publishAt": options.publish_at,

        },
        "recordingDetails": {
            "location": lib.string_to_dict(options.location),
            "recordingDate": options.recording_date,
        },
    }

    debug("Start upload: {0}".format(video_path))
    try:
        video_id = upload_video.upload(youtube, video_path, 
            request_body, progress_callback=progress.callback)
    finally:
        progress.finish()
    return video_id

def get_youtube_handler(options):
    """Return the API Youtube object."""
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
    get_code_callback = (auth.browser.get_code 
        if options.auth_browser else auth.console.get_code)
    return auth.get_resource(client_secrets, credentials,
        get_code_callback=get_code_callback)

def upload(video_path, options):
    """Run the main scripts from the parsed options/args."""
    youtube = get_youtube_handler(options)

    if youtube:
        try:            
            video_id = upload_youtube_video(youtube, options, video_path)
            if options.open_link:
                open_link(video_url)
            if options.thumb:
                youtube.thumbnails().set(videoId=video_id, media_body=options.thumb).execute()
            if options.playlist:
                playlists.add_video_to_playlist(youtube, video_id, 
                    title=lib.to_utf8(options.playlist), privacy=options.privacy)
        except googleapiclient.errors.HttpError as error:
            raise RequestError("Server response: {0}".format(bytes.decode(error.content).strip()))
        return video_id
    else:
        raise AuthenticationError("Cannot get youtube resource")
