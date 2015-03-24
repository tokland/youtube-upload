"""Wrapper for Google OAuth2 API."""
import sys

import apiclient.discovery
import oauth2client
import httplib2

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"

def _get_code_from_prompt(authorize_url):
    """Show authorization URL and return the code the user wrote."""
    message = "Check this link in your browser: {0}".format(authorize_url)
    sys.stderr.write(message + "\n")
    return raw_input("Enter verification code: ").strip()

def _get_credentials_interactively(flow, storage, get_code_callback):
    """Return the credentials asking the user."""
    flow.redirect_uri = oauth2client.client.OOB_CALLBACK_URN
    authorize_url = flow.step1_get_authorize_url()
    code = get_code_callback(authorize_url)
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

def get_resource(client_secrets_file, credentials_file, get_code_callback=None):
    """Authenticate and return a googleapiclient.discovery.Resource object."""
    get_flow = oauth2client.client.flow_from_clientsecrets
    flow = get_flow(client_secrets_file, scope=YOUTUBE_UPLOAD_SCOPE)
    storage = oauth2client.file.Storage(credentials_file)
    get_code = get_code_callback or _get_code_from_prompt
    credentials = _get_credentials(flow, storage, get_code)
    http = credentials.authorize(httplib2.Http())
    return apiclient.discovery.build("youtube", "v3", http=http)
