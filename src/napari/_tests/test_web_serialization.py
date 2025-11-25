from __future__ import annotations

import json
import urllib.request

import numpy as np

from napari.components.viewer_model import ViewerModel
from napari.web import WebViewerServer, serialize_layer, serialize_viewer


def test_serialize_viewer_with_layers() -> None:
    viewer = ViewerModel()
    viewer.title = "demo"
    viewer.add_image(np.zeros((4, 4), dtype=np.uint8), name="image")
    viewer.add_points(np.array([[0, 1], [2, 3]]), name="points")

    payload = serialize_viewer(viewer)

    assert payload["title"] == "demo"
    assert payload["ndisplay"] == viewer.dims.ndisplay
    assert len(payload["layers"]) == 2
    assert payload["layers"][0]["name"] == "image"
    assert payload["layers"][0]["shape"] == [4, 4]


def test_serialize_layer_metadata_roundtrip() -> None:
    viewer = ViewerModel()
    layer = viewer.add_points(np.array([[0.0, 1.0]]), name="points", metadata={"label": "A"})

    payload = serialize_layer(layer)

    assert payload["metadata"] == {"label": "A"}
    assert payload["dtype"]
    assert payload["shape"] == [1, 2]


def test_web_viewer_server_serves_json() -> None:
    viewer = ViewerModel()
    viewer.add_image(np.zeros((2, 2), dtype=np.float32), name="image")

    server = WebViewerServer(viewer)
    with server.run_in_thread():
        with urllib.request.urlopen(f"{server.url}api/viewer") as response:
            assert response.status == 200
            data = json.loads(response.read().decode("utf-8"))

    assert data["layers"][0]["name"] == "image"
