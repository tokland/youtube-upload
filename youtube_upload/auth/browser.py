import lib

try:
    from youtube_upload.auth import webkit_qt
    WEBKIT_BACKEND = "qt"
except ImportError:
    from youtube_upload.auth import webkit_gtk
    WEBKIT_BACKEND = "gtk"
except ImportError:
    WEBKIT_BACKEND = None

def get_code(url, size=(640, 480), title="Google authentication"):
    if WEBKIT_BACKEND == "qt":
        lib.debug("Using webkit backend: QT")
        with lib.default_sigint():
            return webkit_qt.get_code(url, size=size, title=title)
    elif WEBKIT_BACKEND == "gtk":
        lib.debug("Using webkit backend: GTK")
        with lib.default_sigint():
            return webkit_gtk.get_code(url, size=size, title=title)
    else:
        raise NotImplementedError("GUI auth requires pywebkitgtk or qtwebkit")
