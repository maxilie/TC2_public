import threading
import traceback


def synchronized_on_mongo(func):
    """
    Prevents any two functions decorated with "@synchronized_on_mongo" from being run simultaneously
    """
    func.__lock__ = threading.Lock()

    try:
        def synced_func(*args, **kws):
            with func.__lock__:
                return func(*args, **kws)

        return synced_func
    except Exception:
        traceback.print_exc()


def synchronized_on_alpaca(func):
    """Prevents any two functions decorated with "@synchronized_on_alpaca" from being run simultaneously."""
    func.__lock__ = threading.Lock()

    try:
        def synced_func(*args, **kws):
            with func.__lock__:
                return func(*args, **kws)

        return synced_func
    except Exception:
        traceback.print_exc()


def synchronized_on_polygon_rest(func):
    """Prevents any two functions decorated with "@synchronized_on_polygon_rest" from being run simultaneously."""
    func.__lock__ = threading.Lock()

    try:
        def synced_func(*args, **kws):
            with func.__lock__:
                return func(*args, **kws)

        return synced_func
    except Exception:
        traceback.print_exc()
