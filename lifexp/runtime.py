"""Runtime helpers for paths, platform behavior, and HTTPS."""

import os
import ssl
import sys
import tkinter as tk

try:
    import certifi
except ModuleNotFoundError:
    certifi = None

from .constants import APP_NAME, PACKAGED_MACOS_MIN_TK_SCALING


def get_resource_dir():
    """Returns the folder where bundled read-only app assets live."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_user_data_dir():
    """Returns the folder where packaged builds should write user progress."""
    if sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_NAME)
    return os.path.join(os.path.expanduser("~"), f".{APP_NAME.lower()}")


def is_packaged_app():
    """Returns True when LifeXP is running from a frozen packaged build."""
    return getattr(sys, "frozen", False)


def configure_platform_scaling(root):
    """Keeps packaged macOS font rendering close to normal Python Tkinter runs."""
    if sys.platform != "darwin" or not is_packaged_app():
        return
    try:
        current_scaling = float(root.tk.call("tk", "scaling"))
    except (tk.TclError, ValueError):
        return
    if current_scaling < PACKAGED_MACOS_MIN_TK_SCALING:
        root.tk.call("tk", "scaling", PACKAGED_MACOS_MIN_TK_SCALING)


def get_https_context():
    """Returns an HTTPS context that works inside the packaged macOS app."""
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()
