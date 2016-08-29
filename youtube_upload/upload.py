import collections
import os
import sys
import socket
import webbrowser

try:
    import httplib
except ImportError:
    import http.client as httplib

import googleapiclient.errors
import oauth2client
import apiclient.http
import httplib2

from . import lib
from . import playlists
from . import auth
from . import categories

# http://code.google.com/p/python-progressbar (>= 2.3)
try:
    import progressbar
except ImportError:
    progressbar = None

debug = lib.debug
struct = collections.namedtuple

OPTIONS = {
    "title": dict(type=str, description="Video title"),
    "category": dict(type=str, description="Video category"),
    "description": dict(type=str, description="Video description"),
    "tags": dict(type=str, description='Video tags (separated by commas: "tag1, tag2,...")'),
    "privacy": dict(type=str, description="Privacy status (public | unlisted | private)"),
    "publish_at": dict(type=str, description="Publish date (ISO 8601): YYYY-MM-DDThh:mm:ss.sZ"),
    "location": dict(type=str, description="Location: latitude=VAL,longitude=VAL[,altitude=VAL]"),
    "recording_date": dict(type=str, description="Recording date (ISO 8601): YYYY-MM-DDThh:mm:ss.sZ"),
    "default_language": dict(type=str, description="Default language (ISO 639-1: en | fr | de | ...)"),
    "default_audio_language": dict(type=str, description="Default audio language (ISO 639-1: en | fr | de | ...)"),
    "thumb": dict(type=str, description="Image file to use as video thumbnail (JPEG or PNG)"),
    "playlist": dict(type=str, description="Playlist title (if it does not exist, it will be created)"),
    "client_secrets": dict(type=str, description="Client secrets JSON path file"),
    "auth_browser": dict(type=bool, description="Open a url in a web browser to display the uploaded video"),
    "credentials_file": dict(type=str, description="Credentials JSON path file"),
    "open_link": dict(type=str, description="Opens a url in a web browser to display the uploaded video"),
}

Options = struct("YoutubeUploadOptions", OPTIONS.keys())
build_options = Options(*([None] * len(OPTIONS)))._replace

class InvalidCategory(Exception): pass
class AuthenticationError(Exception): pass
class RequestError(Exception): pass

RETRIABLE_EXCEPTIONS = [
    socket.error, IOError, httplib2.HttpLib2Error, httplib.NotConnected,
    httplib.IncompleteRead, httplib.ImproperConnectionState,
    httplib.CannotSendRequest, httplib.CannotSendHeader,
    httplib.ResponseNotReady, httplib.BadStatusLine,
]

def _upload_to_request(request, progress_callback):
    """Upload a video to a Youtube request. Return video ID."""
    while 1:
        status, response = request.next_chunk()
        if status and progress_callback:
            progress_callback(status.total_size, status.resumable_progress)
        if response:
            if "id" in response:
                return response['id']
            else:
                raise KeyError("Expected field 'id' not found in response")

def upload(resource, path, body, chunksize=4*1024*1024, 
        progress_callback=None, max_retries=10):
    """Upload video to Youtube. Return video ID."""
    body_keys = ",".join(body.keys())
    media = apiclient.http.MediaFileUpload(path, chunksize=chunksize, 
        resumable=True, mimetype="application/octet-stream")
    request = resource.videos().insert(part=body_keys, body=body, media_body=media)
    upload_fun = lambda: _upload_to_request(request, progress_callback)
    return lib.retriable_exceptions(upload_fun, 
        RETRIABLE_EXCEPTIONS, max_retries=max_retries)

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
            
def build_body_and_upload(youtube, options, video_path):
    """Upload video."""
    u = lib.to_utf8
    title = u(options.title)
    if hasattr(u('string'), 'decode'):   
        description = u(options.description or "").decode("string-escape")
    else:
        description = options.description
    if options.publish_at:    
      debug("Your video will remain private until specified date.")
      
    tags = [u(s.strip()) for s in (options.tags or "").split(",") if s.strip()]
    progress = get_progress_info()
    category_id = get_category_id(options.category)
    request_body = lib.remove_empty_fields_recursively({
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": category_id,
            "tags": tags,
            "defaultLanguage": options.default_language,
            "defaultAudioLanguage": options.default_audio_language,

        },
        "status": {
            "privacyStatus": ("private" if options.publish_at else (options.privacy or "public")),
            "publishAt": options.publish_at,

        },
        "recordingDetails": {
            "location": lib.string_to_dict(options.location),
            "recordingDate": options.recording_date,
        },
    })

    debug("Start upload: {0}".format(video_path))
    try:
        video_id = upload(youtube, video_path, 
            request_body, progress_callback=progress.callback)
    finally:
        progress.finish()
    return video_id

def get_resource(options):
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

def upload_video(resource, video_path, options):
    """Run the main scripts from the parsed options/args."""
    if resource:
        try:            
            video_id = build_body_and_upload(resource, options, video_path)
            if options.open_link:
                open_link(video_url)
            if options.thumb:
                resource.thumbnails().set(videoId=video_id, media_body=options.thumb).execute()
            if options.playlist:
                playlists.add_video_to_playlist(resource, video_id, 
                    title=lib.to_utf8(options.playlist), privacy=options.privacy)
        except googleapiclient.errors.HttpError as error:
            raise RequestError("Server response: {0}".format(bytes.decode(error.content).strip()))
        return video_id
    else:
        raise AuthenticationError("Cannot get youtube resource")
