import socket

try:
    import httplib
except ImportError:
    import http.client as httplib

import googleapiclient.errors
import apiclient.http
import httplib2

from . import lib

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
