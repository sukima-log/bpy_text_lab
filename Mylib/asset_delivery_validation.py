"""Deterministic delivery checks shared by BPY-generated atomic assets."""

import hashlib
import json
import os

import bpy
from mathutils import Vector


def _world_bbox(objects):
    points = [obj.matrix_world @ Vector(corner)
              for obj in objects if obj.type == 'MESH'
              for corner in obj.bound_box]
    if not points:
        return None
    minimum = [min(point[axis] for point in points) for axis in range(3)]
    maximum = [max(point[axis] for point in points) for axis in range(3)]
    return {
        "min": minimum,
        "max": maximum,
        "size": [maximum[axis] - minimum[axis] for axis in range(3)],
    }


def _relative_similarity(actual, expected):
    return 1.0 - abs(float(actual) - float(expected)) / max(abs(float(expected)), 1.0e-9)


def validate_glb_roundtrip(asset_name, anchor_name, output_path, report_path):
    """Export one atomic asset, reimport it, measure it, and remove the copy."""
    mesh = bpy.data.objects.get(asset_name)
    anchor = bpy.data.objects.get(anchor_name)
    if mesh is None or mesh.type != 'MESH' or anchor is None or anchor.type != 'EMPTY':
        raise RuntimeError("roundtrip requires one named Mesh and one named Empty")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    original_bbox = _world_bbox([mesh])
    original_materials = len([item for item in mesh.data.materials if item is not None])
    original_uv = mesh.data.uv_layers.get("UVMap")
    before = set(bpy.data.objects)
    saved_selection = list(bpy.context.selected_objects)
    saved_active = bpy.context.view_layer.objects.active
    bpy.ops.object.select_all(action='DESELECT')
    mesh.select_set(True)
    anchor.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format='GLB',
        use_selection=True,
        export_apply=False,
        export_materials='EXPORT',
        export_texcoords=True,
        export_normals=True,
        export_tangents=True,
        export_extras=True,
        export_lights=False,
        export_cameras=False,
        export_animations=False,
    )
    bpy.ops.import_scene.gltf(filepath=output_path)
    imported = [obj for obj in bpy.data.objects if obj not in before]
    imported_meshes = [obj for obj in imported if obj.type == 'MESH']
    imported_empties = [obj for obj in imported if obj.type == 'EMPTY']
    imported_bbox = _world_bbox(imported_meshes)
    dimension_scores = [
        _relative_similarity(imported_bbox["size"][axis], original_bbox["size"][axis])
        for axis in range(3)
    ] if imported_bbox is not None else [0.0, 0.0, 0.0]
    imported_materials = sorted({material.name for obj in imported_meshes
                                 for material in obj.data.materials if material})
    imported_uv_layers = sum(len(obj.data.uv_layers) for obj in imported_meshes)
    hierarchy_ok = any(obj.parent is not None and obj.parent.type == 'EMPTY'
                       for obj in imported_meshes)
    report = {
        "asset": asset_name,
        "glb_path": output_path,
        "glb_bytes": os.path.getsize(output_path),
        "glb_sha256": hashlib.sha256(open(output_path, "rb").read()).hexdigest(),
        "original": {
            "mesh_count": 1,
            "empty_count": 1,
            "bbox_size_m": [round(value, 8) for value in original_bbox["size"]],
            "material_count": original_materials,
            "uv_loop_count": len(original_uv.data) if original_uv else 0,
        },
        "reimported": {
            "mesh_count": len(imported_meshes),
            "empty_count": len(imported_empties),
            "bbox_size_m": [round(value, 8) for value in imported_bbox["size"]]
                            if imported_bbox else None,
            "material_count": len(imported_materials),
            "uv_layer_count": imported_uv_layers,
            "mesh_parented_to_empty": hierarchy_ok,
        },
        "dimension_similarity": [round(value, 8) for value in dimension_scores],
    }
    report["passed"] = (
        len(imported_meshes) == 1
        and len(imported_empties) >= 1
        and hierarchy_ok
        and imported_uv_layers >= 1
        and len(imported_materials) >= original_materials
        and min(dimension_scores) >= 0.99
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in imported:
        bpy.data.objects.remove(obj, do_unlink=True)
    for obj in saved_selection:
        if obj.name in bpy.data.objects:
            obj.select_set(True)
    if saved_active is not None and saved_active.name in bpy.data.objects:
        bpy.context.view_layer.objects.active = saved_active
    return report
