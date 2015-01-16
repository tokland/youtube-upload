import time
import random
import httplib

import apiclient.http
import httplib2

import lib

RETRIABLE_EXCEPTIONS = [
    httplib2.HttpLib2Error, IOError, httplib.NotConnected,
    httplib.IncompleteRead, httplib.ImproperConnectionState,
    httplib.CannotSendRequest, httplib.CannotSendHeader,
    httplib.ResponseNotReady, httplib.BadStatusLine,
]

def with_retriable_exceptions(retriable_exceptions, max_retries=None):
    """Decorate a funcion with a a retry mechanism (exponential backoff)."""
    def _decorator(f):
        def _wrapper(*args, **kwargs):
            retry = 0
            while 1:
                try:
                    return f(*args, **kwargs)
                except tuple(retriable_exceptions) as exc:
                    retry += 1
                    if type(exc) not in retriable_exceptions:
                        raise exc
                    elif max_retries is not None and retry > max_retries:
                        lib.debug("Retry limit reached, time to give up")
                        raise exc
                    seconds = random.uniform(0, 2**retry)
                    lib.debug("Retryable error {}/{}: {}. Waiting {} seconds".
                        format(retry, max_retries or "inf", type(exc).__name__, seconds))
                    time.sleep(seconds)
        return _wrapper
    return _decorator

@with_retriable_exceptions(RETRIABLE_EXCEPTIONS, max_retries=10)
def _upload_to_request(request, progress_callback):
    """Upload a video to a Youtube request. Return video ID."""
    while 1:
        status, response = request.next_chunk()
        if response:
            if "id" in response:
                return response['id']
            else:
                raise KeyError("Response has no 'id' field")
        elif status and progress_callback:
            progress_callback(status.total_size, status.resumable_progress)
        
def upload(resource, path, body, chunksize=int(1e6), progress_callback=None):
    """Upload video to Youtube. Return video ID."""
    body_keys = ",".join(body.keys())
    media = apiclient.http.MediaFileUpload(path, chunksize=chunksize, resumable=True)
    videos = resource.videos()
    request = videos.insert(part=body_keys, body=body, media_body=media)
    return _upload_to_request(request, progress_callback)
