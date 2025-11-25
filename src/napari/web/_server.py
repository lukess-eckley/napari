"""Minimal HTTP server exposing viewer state to a web client."""
from __future__ import annotations

import contextlib
import http.server
import json
import socket
import socketserver
import threading
import time
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator
from urllib.parse import urlparse

from http import HTTPStatus

from ._serialization import serialize_viewer

if TYPE_CHECKING:  # pragma: no cover
    from napari.components.viewer_model import ViewerModel


STATIC_DIR = Path(__file__).with_name("static")


class _RequestHandler(http.server.SimpleHTTPRequestHandler):
    viewer: "ViewerModel | None" = None
    static_root: Path = STATIC_DIR

    def translate_path(self, path: str) -> str:  # pragma: no cover - exercised indirectly
        parsed = urlparse(path)
        if parsed.path == "/":
            target = "index.html"
        else:
            target = parsed.path.lstrip("/")
        return str(self.static_root / target)

    def do_GET(self) -> None:  # pragma: no cover - exercised indirectly
        parsed = urlparse(self.path)
        if parsed.path == "/api/viewer":
            self._handle_viewer()
            return
        super().do_GET()

    def log_message(self, format: str, *args: Any) -> None:  # pragma: no cover - reduce noise
        return

    def _handle_viewer(self) -> None:
        if self.viewer is None:
            self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "No viewer attached")
            return

        payload = json.dumps(serialize_viewer(self.viewer)).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class WebViewerServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Threaded HTTP server that exposes napari viewer state."""

    daemon_threads = True

    def __init__(
        self,
        viewer: "ViewerModel",
        host: str = "127.0.0.1",
        port: int = 0,
    ) -> None:
        handler = type("NapariWebRequestHandler", (_RequestHandler,), {})
        handler.viewer = viewer
        handler.static_root = STATIC_DIR
        super().__init__((host, port), handler)
        self._thread: threading.Thread | None = None

    @property
    def url(self) -> str:
        host, port = self.server_address[:2]
        if host in ("0.0.0.0", "::"):
            host = "127.0.0.1"
        return f"http://{host}:{port}/"

    def start_in_thread(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            raise RuntimeError("Server already running")

        self._thread = threading.Thread(target=self.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.shutdown()
        self.server_close()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    @contextlib.contextmanager
    def run_in_thread(self) -> Iterator["WebViewerServer"]:
        self.start_in_thread()
        try:
            # give the server a short moment to bind the socket
            time.sleep(0.05)
            yield self
        finally:
            self.stop()


def _reserve_port(host: str, port: int) -> tuple[str, int]:
    if port:
        return host, port
    with socket.socket() as sock:
        sock.bind((host, 0))
        return sock.getsockname()[0], sock.getsockname()[1]


def launch_web_viewer(
    viewer: "ViewerModel",
    *,
    host: str = "127.0.0.1",
    port: int = 0,
    open_browser: bool = True,
) -> WebViewerServer:
    """Launch a :class:`WebViewerServer` for *viewer* and optionally open a browser."""

    host, port = _reserve_port(host, port)
    server = WebViewerServer(viewer, host=host, port=port)
    server.start_in_thread()
    if open_browser:
        webbrowser.open(server.url)
    return server

