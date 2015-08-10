"""Wrapper for Google OAuth2 API."""
import sys
import json

import googleapiclient.discovery
import oauth2client
import httplib2 

from youtube_upload import lib
from youtube_upload.auth import console
from youtube_upload.auth import browser

YOUTUBE_UPLOAD_SCOPE = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]

def _get_credentials_interactively(flow, storage, get_code_callback):
    """Return the credentials asking the user."""
    flow.redirect_uri = oauth2client.client.OOB_CALLBACK_URN
    authorize_url = flow.step1_get_authorize_url()
    code = get_code_callback(authorize_url)
    if code:
        credential = flow.step2_exchange(code, http=None)
        storage.put(credential)
        credential.set_store(storage)
        return credential

def _get_credentials(flow, storage, get_code_callback):
    """Return the user credentials. If not found, run the interactive flow."""
    existing_credentials = storage.get()
    if existing_credentials and not existing_credentials.invalid:
        return existing_credentials
    else:
        return _get_credentials_interactively(flow, storage, get_code_callback)

def get_resource(client_secrets_file, credentials_file, get_code_callback):
    """Authenticate and return a googleapiclient.discovery.Resource object."""
    get_flow = oauth2client.client.flow_from_clientsecrets
    flow = get_flow(client_secrets_file, scope=YOUTUBE_UPLOAD_SCOPE)
    storage = oauth2client.file.Storage(credentials_file)
    credentials = _get_credentials(flow, storage, get_code_callback)
    if credentials:
        http = credentials.authorize(httplib2.Http())
        return googleapiclient.discovery.build("youtube", "v3", http=http)
