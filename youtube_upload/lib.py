import sys
import locale
import random
import time

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
    if string:
        pairs = [s.strip() for s in string.split(",")]
        return dict(pair.split("=") for pair in pairs)

def retriable_exceptions(fun, retriable_exceptions, max_retries=None):
    """Run function and retry on some exceptions (with exponential backoff)."""
    retry = 0
    while 1:
        try:
            return fun()
        except tuple(retriable_exceptions) as exc:
            retry += 1
            if type(exc) not in retriable_exceptions:
                raise exc
            elif max_retries is not None and retry > max_retries:
                debug("Retry limit reached, time to give up")
                raise exc
            else:
                seconds = random.uniform(0, 2**retry)
                debug("Retryable error {0}/{1}: {2}. Waiting {3} seconds".
                    format(retry, max_retries or "-", type(exc).__name__, seconds))
                time.sleep(seconds)
