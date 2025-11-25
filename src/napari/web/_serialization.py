"""Utilities for converting napari viewer state into JSON-serialisable data."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Iterable

from napari.components.viewer_model import ViewerModel
from napari.layers import Layer


def serialize_viewer(viewer: ViewerModel) -> dict[str, Any]:
    """Return a JSON-serialisable summary of a :class:`ViewerModel`.

    The structure is intentionally compact so it can be consumed easily by a
    lightweight web client. Only descriptive metadata is included – the raw
    pixel data of the individual layers is *not* transferred.
    """

    dims = viewer.dims
    canvas_size = getattr(viewer, "canvas_size", getattr(viewer, "_canvas_size", ()))

    return {
        "title": viewer.title,
        "theme": viewer.theme,
        "status": viewer.status,
        "ndisplay": dims.ndisplay,
        "axis_labels": list(dims.axis_labels),
        "current_step": list(dims.current_step),
        "canvas_size": list(canvas_size) if canvas_size else [],
        "layers": [serialize_layer(layer) for layer in viewer.layers],
    }


def serialize_layer(layer: Layer) -> dict[str, Any]:
    """Return a compact description of *layer* suitable for JSON output."""

    extent_world = getattr(layer.extent, "world", None)
    extent = _sequence_to_list(extent_world) if extent_world is not None else []

    return {
        "name": layer.name,
        "type": layer.__class__.__name__,
        "visible": layer.visible,
        "opacity": layer.opacity,
        "blending": str(layer.blending.value)
        if hasattr(layer.blending, "value")
        else str(layer.blending),
        "ndim": layer.ndim,
        "shape": _shape_of(layer.data),
        "dtype": _dtype_of(layer.data),
        "scale": _sequence_to_list(layer.scale),
        "translate": _sequence_to_list(layer.translate),
        "source": _describe_source(layer),
        "metadata": _simplify_mapping(layer.metadata),
        "extent": extent,
    }


def _shape_of(data: Any) -> list[int]:
    shape = getattr(data, "shape", None)
    if shape is not None:
        try:
            return [int(v) for v in shape]
        except TypeError:
            pass

    if isinstance(data, Sequence) and not isinstance(data, (str, bytes, bytearray)):
        try:
            return [len(data)]
        except TypeError:
            return []

    return []


def _dtype_of(data: Any) -> str:
    dtype = getattr(data, "dtype", None)
    if dtype is None:
        return ""
    return str(dtype)


def _sequence_to_list(values: Iterable[Any]) -> list[Any]:
    if values is None:
        return []
    return [_coerce_json_value(v) for v in values]


def _simplify_mapping(mapping: Mapping[Any, Any] | None) -> dict[str, Any]:
    if not mapping:
        return {}

    simplified: dict[str, Any] = {}
    for key, value in mapping.items():
        simplified[str(key)] = _coerce_json_value(value)
    return simplified


def _coerce_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _simplify_mapping(value)

    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return [_coerce_json_value(v) for v in value]

    if hasattr(value, "item") and callable(value.item):
        try:
            return value.item()
        except Exception:  # pragma: no cover - defensive
            return str(value)

    if hasattr(value, "tolist") and callable(value.tolist):
        try:
            return value.tolist()
        except Exception:  # pragma: no cover - defensive
            return str(value)

    return value


def _describe_source(layer: Layer) -> dict[str, Any]:
    source = getattr(layer, "source", None)
    if source is None:
        return {}

    description: dict[str, Any] = {
        "path": getattr(source, "path", None),
        "reader_plugin": getattr(source, "reader_plugin", None),
        "sample": getattr(source, "sample", None),
    }
    return {k: v for k, v in description.items() if v is not None}

