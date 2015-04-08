"""Wrapper for Google OAuth2 API."""
import sys
import json

import gtk
import webkit
import googleapiclient.discovery
import oauth2client
import httplib2

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"

JAVASCRIPT_AUTHORIZATION_SET_STATUS = """
    var code = document.getElementById("code");
    var access_denied = document.getElementById("access_denied");
    var result;
    
    if (code) {
        result = {authorized: true, code: code.value};
    } else if (access_denied) {
        result = {authorized: false, message: access_denied.innerText};
    } else {
        result = {};
    }
    window.status = JSON.stringify(result);
"""

def _on_webview_status_bar_changed(webview, status, dialog):
    if status:
        result = json.loads(status)
        if result.has_key("authorized"):
            dialog.set_data("authorization", result)
            dialog.response(0)
    
def _get_code_from_browser(url, size=(640, 480), title=None):
    """Open a webkit window and return the code the user wrote."""
    webview = webkit.WebView()
    dialog = gtk.Dialog(title=(title or "Google authentication"))
    scrolled = gtk.ScrolledWindow()
    scrolled.add(webview)
    dialog.get_children()[0].add(scrolled)
    webview.load_uri(url)    
    dialog.resize(*size)
    dialog.show_all()
    
    dialog.connect("delete-event", lambda ev, data: dialog.response(1))
    webview.connect("load-finished", 
        lambda view, frame: webview.execute_script(JAVASCRIPT_AUTHORIZATION_SET_STATUS))       
    webview.connect("status-bar-text-changed", _on_webview_status_bar_changed, dialog)
    dialog.set_data("authorization", None)
    status = dialog.run()
    dialog.destroy()
    while gtk.events_pending():
        gtk.main_iteration(False)
    authorization = dialog.get_data("authorization")    
    if status == 0 and authorization and authorization["authorized"]:
        return authorization["code"]
        
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

def get_resource(client_secrets_file, credentials_file, get_code_callback=None):
    """Authenticate and return a googleapiclient.discovery.Resource object."""
    get_flow = oauth2client.client.flow_from_clientsecrets
    flow = get_flow(client_secrets_file, scope=YOUTUBE_UPLOAD_SCOPE)
    storage = oauth2client.file.Storage(credentials_file)
    get_code = get_code_callback or _get_code_from_prompt
    credentials = _get_credentials(flow, storage, get_code)
    if credentials:
        http = credentials.authorize(httplib2.Http())
        return googleapiclient.discovery.build("youtube", "v3", http=http)
