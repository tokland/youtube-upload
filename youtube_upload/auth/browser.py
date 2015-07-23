from .. import lib

try:
    from youtube_upload.auth import webkit_qt as backend
    WEBKIT_BACKEND = "qt"
except ImportError:
    try:
        from youtube_upload.auth import webkit_gtk as backend
        WEBKIT_BACKEND = "gtk"
    except ImportError:
        WEBKIT_BACKEND = None

def get_code(url, size=(640, 480), title="Google authentication"):
    if WEBKIT_BACKEND:
        lib.debug("Using webkit backend: " + WEBKIT_BACKEND)
        with lib.default_sigint():
            return backend.get_code(url, size=size, title=title)
    else:
        raise NotImplementedError("GUI auth requires pywebkitgtk or qtwebkit")
