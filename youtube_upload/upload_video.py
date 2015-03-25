import time
import random
import httplib

import apiclient.http
import httplib2
from googleapiclient.errors import ResumableUploadError

import lib

RETRIABLE_EXCEPTIONS = [
    httplib2.HttpLib2Error, IOError, httplib.NotConnected,
    httplib.IncompleteRead, httplib.ImproperConnectionState,
    httplib.CannotSendRequest, httplib.CannotSendHeader,
    httplib.ResponseNotReady, httplib.BadStatusLine,
    ResumableUploadError
]

def _upload_to_request(request, progress_callback):
    """Upload a video to a Youtube request. Return video ID."""
    while 1:
        status, response = request.next_chunk()
        if response:
            if "id" in response:
                return response['id']
            else:
                raise KeyError("The response has no 'id' field")
        elif status and progress_callback:
            progress_callback(status.total_size, status.resumable_progress)
        
def upload(resource, path, body, chunksize=int(1e6), progress_callback=None):
    """Upload video to Youtube. Return video ID."""
    body_keys = ",".join(body.keys())
    media = apiclient.http.MediaFileUpload(path, chunksize=chunksize, 
        resumable=True, mimetype="application/octet-stream")
    request = resource.videos().insert(part=body_keys, body=body, media_body=media)
    upload_fun = lambda: _upload_to_request(request, progress_callback)
    return lib.retriable_exceptions(upload_fun, RETRIABLE_EXCEPTIONS, max_retries=10)
