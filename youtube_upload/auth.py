"""Wrapper for Google OAuth2 API."""
import sys
import json

import googleapiclient.discovery
import oauth2client
import httplib2

import lib

try:
    from PyQt4 import QtCore, QtGui, QtWebKit
    WEBKIT_BACKEND = "qt"
except ImportError:
    import gtk
    import webkit
    WEBKIT_BACKEND = "gtk"
except ImportError:
    WEBKIT_BACKEND = None

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"

CHECK_AUTH_JS = """
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
"""

CHECK_AUTH_JS_GTK = CHECK_AUTH_JS + "window.status = JSON.stringify(result);"
CHECK_AUTH_JS_QT = CHECK_AUTH_JS + "result;"

def _get_code_from_browser(url, size=(640, 480), title="Google authentication"):
    if WEBKIT_BACKEND == "qt":
        lib.debug("Using webkit backend: QT")
        with lib.default_sigint():
            return _get_code_from_browser_qt(url, size=size, title=title)
    elif WEBKIT_BACKEND == "gtk":
        lib.debug("Using webkit backend: GTK")
        return _get_code_from_browser_gtk(url, size=size, title=title)
    else:
        raise NotImplementedError("Install pywebkitgtk or qtwebkit")
   
def on_qt_page_load_finished(dialog, webview):
    to_s = lambda x: (str(x.toUtf8()) if isinstance(x, QtCore.QString) else x)
    frame = webview.page().currentFrame()
    jscode = QtCore.QString(CHECK_AUTH_JS_QT)
    res = frame.evaluateJavaScript(jscode)
    authorization = dict((to_s(k), to_s(v)) for (k, v) in res.toPyObject().items())
    if authorization:
        dialog.authorization_code = authorization.get("code")
        dialog.close()
   
def _get_code_from_browser_qt(url, size=(640, 480), title="Google authentication"):
    app = QtGui.QApplication(sys.argv)
    dialog = QtGui.QDialog()
    dialog.setWindowTitle(title)
    dialog.resize(*size)
    webview = QtWebKit.QWebView()
    webpage = QtWebKit.QWebPage()
    webview.setPage(webpage)           
    webpage.loadFinished.connect(lambda: on_qt_page_load_finished(dialog, webview))
    webview.setUrl(QtCore.QUrl.fromEncoded(url))
    layout = QtGui.QGridLayout()
    layout.addWidget(webview)
    dialog.setLayout(layout)
    dialog.authorization_code = None
    dialog.show()
    app.exec_()
    return dialog.authorization_code    

def _on_webview_status_bar_changed(webview, status, dialog):
    if status:
        result = json.loads(status)
        if result.has_key("authorized"):
            dialog.set_data("authorization", result)
            dialog.response(0)
    
def _get_code_from_browser_gtk(url, size=(640, 480), title="Google authentication"):
    """Open a webkit window and return the code the user wrote."""
    dialog = gtk.Dialog(title=title)
    webview = webkit.WebView()
    scrolled = gtk.ScrolledWindow()
    scrolled.add(webview)
    dialog.get_children()[0].add(scrolled)
    webview.load_uri(url)    
    dialog.resize(*size)
    dialog.show_all()
    
    dialog.connect("delete-event", lambda event, data: dialog.response(1))
    webview.connect("load-finished", 
        lambda view, frame: view.execute_script(CHECK_AUTH_JS))       
    webview.connect("status-bar-text-changed", _on_webview_status_bar_changed, dialog)
    dialog.set_data("authorization", None)
    
    status = dialog.run()
    dialog.destroy()
    while gtk.events_pending():
        gtk.main_iteration(False)
    authorization = dialog.get_data("authorization")    
    if status == 0 and authorization and authorization.get("authorized"):
        return authorization["code"]
        
def _get_code_from_prompt(authorize_url):
    """Show authorization URL and return the code the user wrote."""
    message = "Check this link in your browser: {0}".format(authorize_url)
    lib.debug(message)
    return raw_input("Enter verification code: ")

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
