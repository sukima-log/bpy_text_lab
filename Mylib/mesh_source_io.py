"""Deterministic text mesh source import/export for BPY_3DCG_ENV.

The accepted geometry source is stored as a small manifest and one JSON Lines
file per mesh object.  Files are regular UTF-8 text, so they can be reviewed
and versioned by normal Git without Git LFS.

This format intentionally owns only the d00 geometry boundary: vertex
positions, polygon topology, material slot names/indices, smooth flags, object
transforms, and selected POINT-domain mesh attributes.  UVs and production
materials remain the responsibility of d01 and d02.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from pathlib import Path
from typing import Iterable, Sequence

import bpy
from mathutils import Matrix


SCHEMA_NAME = "bpy_text_mesh_bundle"
SCHEMA_VERSION = 1
DEFAULT_COORDINATE_STEP = 0.000001
DEFAULT_MAX_OBJECT_FILE_BYTES = 80 * 1024 * 1024
SUPPORTED_POINT_ATTRIBUTE_TYPES = {
    "FLOAT": "value",
    "INT": "value",
    "BOOLEAN": "value",
    "FLOAT_VECTOR": "vector",
    "FLOAT_COLOR": "color",
    "BYTE_COLOR": "color",
}


def _json_line(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as file_pointer:
        for chunk in iter(lambda: file_pointer.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_file_stem(name):
    stem = re.sub(r"[^0-9A-Za-z._-]+", "_", name).strip("._")
    return stem or "mesh"


def _quantize(value, coordinate_step):
    if not math.isfinite(value):
        raise ValueError("Mesh source cannot contain NaN or infinite coordinates")
    return int(round(value / coordinate_step))


def _attribute_value(attribute_data, field_name):
    value = getattr(attribute_data, field_name)
    if field_name in {"vector", "color"}:
        return [round(float(component), 8) for component in value]
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    return round(float(value), 8)


def _point_attribute_specs(mesh, attribute_names):
    specs = []
    allowed_names = set(attribute_names or [])
    for attribute in mesh.attributes:
        if attribute.domain != "POINT":
            continue
        if attribute.name in {"position", ".select_vert"}:
            continue
        if allowed_names and attribute.name not in allowed_names:
            continue
        field_name = SUPPORTED_POINT_ATTRIBUTE_TYPES.get(attribute.data_type)
        if field_name is None:
            continue
        specs.append(
            {
                "name": attribute.name,
                "data_type": attribute.data_type,
                "field": field_name,
            }
        )
    return sorted(specs, key=lambda item: item["name"])


def _write_mesh_object(
    *,
    obj,
    path,
    coordinate_step,
    point_attribute_names,
    max_object_file_bytes,
):
    if obj.type != "MESH":
        raise TypeError(f"Expected MESH object, got {obj.type}: {obj.name}")

    mesh = obj.data
    attribute_specs = _point_attribute_specs(mesh, point_attribute_names)
    header = {
        "record": "header",
        "schema": SCHEMA_NAME,
        "version": SCHEMA_VERSION,
        "object_name": obj.name,
        "mesh_name": mesh.name,
        "coordinate_step": coordinate_step,
        "vertex_count": len(mesh.vertices),
        "polygon_count": len(mesh.polygons),
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "point_attributes": attribute_specs,
    }

    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with open(temporary_path, "w", encoding="utf-8", newline="\n") as file_pointer:
        file_pointer.write(_json_line(header) + "\n")
        for vertex in mesh.vertices:
            attributes = {}
            for spec in attribute_specs:
                attribute = mesh.attributes[spec["name"]]
                attributes[spec["name"]] = _attribute_value(
                    attribute.data[vertex.index],
                    spec["field"],
                )
            record = [
                "v",
                _quantize(vertex.co.x, coordinate_step),
                _quantize(vertex.co.y, coordinate_step),
                _quantize(vertex.co.z, coordinate_step),
            ]
            if attributes:
                record.append(attributes)
            file_pointer.write(_json_line(record) + "\n")

        for polygon in mesh.polygons:
            record = [
                "f",
                int(polygon.material_index),
                bool(polygon.use_smooth),
                *[int(index) for index in polygon.vertices],
            ]
            file_pointer.write(_json_line(record) + "\n")

    file_size = temporary_path.stat().st_size
    if file_size > max_object_file_bytes:
        temporary_path.unlink()
        raise ValueError(
            f"Mesh source exceeds {max_object_file_bytes} bytes: "
            f"{path.name} ({file_size} bytes). Split it into semantic objects."
        )
    os.replace(temporary_path, path)
    return {
        "name": obj.name,
        "file": path.name,
        "sha256": _sha256(path),
        "matrix_world": [
            [round(float(component), 9) for component in row]
            for row in obj.matrix_world
        ],
        "vertex_count": len(mesh.vertices),
        "polygon_count": len(mesh.polygons),
    }


def export_mesh_bundle(
    *,
    objects: Iterable,
    output_directory,
    asset_name,
    coordinate_step=DEFAULT_COORDINATE_STEP,
    point_attribute_names: Sequence[str] | None = None,
    max_object_file_bytes=DEFAULT_MAX_OBJECT_FILE_BYTES,
):
    """Export accepted d00 geometry as deterministic, Git-friendly text.

    Keep semantic parts as separate objects during export.  The d00 asset
    function may join them into the final one-Mesh representation after load.
    """

    if coordinate_step <= 0.0:
        raise ValueError("coordinate_step must be positive")

    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    mesh_objects = sorted(
        [obj for obj in objects if obj.type == "MESH"],
        key=lambda obj: obj.name,
    )
    if not mesh_objects:
        raise ValueError("No mesh objects were supplied for export")
    bpy.context.view_layer.update()

    object_records = []
    used_file_names = set()
    for index, obj in enumerate(mesh_objects):
        stem = _safe_file_stem(obj.name)
        file_name = f"{index:03d}_{stem}.mesh.jsonl"
        if file_name in used_file_names:
            raise ValueError(f"Duplicate mesh source file name: {file_name}")
        used_file_names.add(file_name)
        object_records.append(
            _write_mesh_object(
                obj=obj,
                path=directory / file_name,
                coordinate_step=coordinate_step,
                point_attribute_names=point_attribute_names,
                max_object_file_bytes=max_object_file_bytes,
            )
        )

    manifest = {
        "schema": SCHEMA_NAME,
        "version": SCHEMA_VERSION,
        "asset_name": asset_name,
        "blender_version": list(bpy.app.version),
        "coordinate_system": "Blender Z-up right-handed; object local vertices plus matrix_world",
        "objects": object_records,
    }
    manifest_path = directory / "manifest.json"
    temporary_path = directory / "manifest.json.tmp"
    with open(temporary_path, "w", encoding="utf-8", newline="\n") as file_pointer:
        json.dump(manifest, file_pointer, ensure_ascii=False, indent=2, sort_keys=True)
        file_pointer.write("\n")
    os.replace(temporary_path, manifest_path)
    return manifest_path


def _read_mesh_object(*, path, expected_sha256, collection, object_name_override=None):
    if _sha256(path) != expected_sha256:
        raise ValueError(f"Mesh source checksum mismatch: {path}")

    with open(path, "r", encoding="utf-8") as file_pointer:
        header = json.loads(file_pointer.readline())
        if header.get("schema") != SCHEMA_NAME or header.get("version") != SCHEMA_VERSION:
            raise ValueError(f"Unsupported mesh source schema: {path}")

        coordinate_step = float(header["coordinate_step"])
        vertices = []
        faces = []
        material_indices = []
        smooth_flags = []
        attribute_values = {
            spec["name"]: [] for spec in header.get("point_attributes", [])
        }

        for line_number, line in enumerate(file_pointer, start=2):
            if not line.strip():
                continue
            record = json.loads(line)
            if record[0] == "v":
                vertices.append(
                    (
                        record[1] * coordinate_step,
                        record[2] * coordinate_step,
                        record[3] * coordinate_step,
                    )
                )
                attributes = record[4] if len(record) > 4 else {}
                for name in attribute_values:
                    if name not in attributes:
                        raise ValueError(f"Missing point attribute {name} at {path}:{line_number}")
                    attribute_values[name].append(attributes[name])
            elif record[0] == "f":
                material_indices.append(int(record[1]))
                smooth_flags.append(bool(record[2]))
                faces.append([int(index) for index in record[3:]])
            else:
                raise ValueError(f"Unknown mesh record at {path}:{line_number}")

    if len(vertices) != int(header["vertex_count"]):
        raise ValueError(f"Vertex count mismatch: {path}")
    if len(faces) != int(header["polygon_count"]):
        raise ValueError(f"Polygon count mismatch: {path}")
    if any(index < 0 or index >= len(vertices) for face in faces for index in face):
        raise ValueError(f"Face contains an invalid vertex index: {path}")

    mesh_name = header.get("mesh_name") or header["object_name"]
    mesh = bpy.data.meshes.new(name=mesh_name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)

    object_name = object_name_override or header["object_name"]
    obj = bpy.data.objects.new(object_name, mesh)
    collection.objects.link(obj)
    for material_name in header.get("materials", []):
        material = None
        if material_name:
            material = bpy.data.materials.get(material_name) or bpy.data.materials.new(material_name)
        mesh.materials.append(material)

    for polygon, material_index, smooth_flag in zip(
        mesh.polygons,
        material_indices,
        smooth_flags,
    ):
        polygon.material_index = material_index
        polygon.use_smooth = smooth_flag

    for spec in header.get("point_attributes", []):
        attribute = mesh.attributes.new(
            name=spec["name"],
            type=spec["data_type"],
            domain="POINT",
        )
        field_name = spec["field"]
        for target, value in zip(attribute.data, attribute_values[spec["name"]]):
            setattr(target, field_name, value)

    mesh.validate(verbose=False, clean_customdata=False)
    mesh.update(calc_edges=True)
    return obj


def load_mesh_bundle(
    *,
    source_directory,
    collection=None,
    object_name_prefix=None,
):
    """Restore a text mesh bundle and return the created mesh objects."""

    directory = Path(source_directory)
    manifest_path = directory / "manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as file_pointer:
        manifest = json.load(file_pointer)
    if manifest.get("schema") != SCHEMA_NAME or manifest.get("version") != SCHEMA_VERSION:
        raise ValueError(f"Unsupported mesh bundle schema: {manifest_path}")

    target_collection = collection or bpy.context.collection
    objects = []
    for object_record in manifest["objects"]:
        source_name = object_record["name"]
        object_name = f"{object_name_prefix}{source_name}" if object_name_prefix else source_name
        obj = _read_mesh_object(
            path=directory / object_record["file"],
            expected_sha256=object_record["sha256"],
            collection=target_collection,
            object_name_override=object_name,
        )
        obj.matrix_world = Matrix(object_record["matrix_world"])
        objects.append(obj)
    return objects


def verify_mesh_bundle(*, source_directory):
    """Validate schema, checksums, and declared file budgets without creating objects."""

    directory = Path(source_directory)
    manifest_path = directory / "manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as file_pointer:
        manifest = json.load(file_pointer)
    if manifest.get("schema") != SCHEMA_NAME or manifest.get("version") != SCHEMA_VERSION:
        raise ValueError(f"Unsupported mesh bundle schema: {manifest_path}")
    for object_record in manifest["objects"]:
        path = directory / object_record["file"]
        if not path.is_file():
            raise FileNotFoundError(path)
        if _sha256(path) != object_record["sha256"]:
            raise ValueError(f"Mesh source checksum mismatch: {path}")
    return manifest
