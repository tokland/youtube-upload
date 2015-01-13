import sys
import locale

def to_utf8(s):
    """Re-encode string from the default system encoding to UTF-8."""
    current = locale.getpreferredencoding()
    return s.decode(current).encode("UTF-8") if s and current != "UTF-8" else s

def debug(obj, fd=sys.stderr):
    """Write obj to standard error."""
    string = str(obj.encode(get_encoding(fd), "backslashreplace")
                 if isinstance(obj, unicode) else obj)
    fd.write(string + "\n")

def catch_exceptions(exit_codes, fun, *args, **kwargs):
    """
    Catch exceptions on fun(*args, **kwargs) and return the exit code specified
    in the exit_codes dictionary. Return 0 if no exception is raised.
    """
    try:
        fun(*args, **kwargs)
        return 0
    except tuple(exit_codes.keys()) as exc:
        debug("[%s] %s" % (exc.__class__.__name__, exc))
        return exit_codes[exc.__class__]

def get_encoding(fd):
    """Guess terminal encoding."""
    return fd.encoding or locale.getpreferredencoding()

def first(it):
    """Return first element in iterable."""
    return it.next()

def string_to_dict(string):
    """Return dictionary from string "key1=value1, key2=value2"."""
    pairs = [s.strip() for s in (string or "").split(",")]
    return dict(pair.split("=") for pair in pairs)
