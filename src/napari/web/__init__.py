"""Simple web-based presentation layer for napari viewers."""
from __future__ import annotations

from ._serialization import serialize_layer, serialize_viewer
from ._server import WebViewerServer, launch_web_viewer

__all__ = [
    "WebViewerServer",
    "launch_web_viewer",
    "serialize_layer",
    "serialize_viewer",
]
