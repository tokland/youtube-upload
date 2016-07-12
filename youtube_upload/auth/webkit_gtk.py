import json

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
    window.status = JSON.stringify(result);
"""

def _on_webview_status_bar_changed(webview, status, dialog):
    if status:
        authorization = json.loads(status)
        if authorization.has_key("authorized"):
            dialog.set_data("authorization_code", authorization["code"])
            dialog.response(0)

def get_code(url, size=(640, 480), title="Google authentication"):
    """Open a GTK webkit window and return the access code."""
    import gtk
    import webkit
    dialog = gtk.Dialog(title=title)
    webview = webkit.WebView()
    scrolled = gtk.ScrolledWindow()
    scrolled.add(webview)
    dialog.get_children()[0].add(scrolled)
    webview.load_uri(url)    
    dialog.resize(*size)
    dialog.show_all()
    dialog.connect("delete-event", 
        lambda event, data: dialog.response(1))
    webview.connect("load-finished", 
        lambda view, frame: view.execute_script(CHECK_AUTH_JS))       
    webview.connect("status-bar-text-changed", 
        _on_webview_status_bar_changed, dialog)
    dialog.set_data("authorization_code", None)
    status = dialog.run()
    dialog.destroy()
    while gtk.events_pending():
        gtk.main_iteration(False)
    return dialog.get_data("authorization_code")
