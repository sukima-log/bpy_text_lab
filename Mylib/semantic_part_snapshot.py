"""Export a Git-reproducible semantic-part snapshot before final GLB flattening.

The production asset may remain one Mesh below one Empty.  This helper creates
temporary per-owner meshes from a FACE-domain integer attribute, exports them,
verifies the GLB reimport, and removes the temporary scene objects.
"""

from __future__ import annotations

import hashlib
import json
import os
import re

import bpy
from mathutils import Matrix


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _subset_mesh(source, polygon_indices, mesh_name):
    source_mesh = source.data
    source_polygons = [source_mesh.polygons[index] for index in polygon_indices]
    used_vertices = sorted({
        vertex_index
        for polygon in source_polygons
        for vertex_index in polygon.vertices
    })
    remap = {old_index: new_index for new_index, old_index in enumerate(used_vertices)}
    vertices = [source_mesh.vertices[index].co[:] for index in used_vertices]
    faces = [
        [remap[vertex_index] for vertex_index in polygon.vertices]
        for polygon in source_polygons
    ]

    target_mesh = bpy.data.meshes.new(mesh_name)
    target_mesh.from_pydata(vertices, [], faces)
    target_mesh.update()
    for material in source_mesh.materials:
        target_mesh.materials.append(material)
    for target_polygon, source_polygon in zip(target_mesh.polygons, source_polygons):
        target_polygon.material_index = source_polygon.material_index
        target_polygon.use_smooth = source_polygon.use_smooth

    for source_uv in source_mesh.uv_layers:
        target_uv = target_mesh.uv_layers.new(name=source_uv.name)
        for target_polygon, source_polygon in zip(target_mesh.polygons, source_polygons):
            for target_loop, source_loop in zip(
                target_polygon.loop_indices, source_polygon.loop_indices
            ):
                target_uv.data[target_loop].uv = source_uv.data[source_loop].uv
    return target_mesh


def _canonical_world_union_sha256(objects, precision=8):
    """Return one object-boundary-independent hash for unchanged source geometry.

    Input:
        objects   : Mesh objects whose current evaluated copies are being audited.
        precision : Decimal places used for deterministic world-space rounding.
    Output:
        SHA-256 over the full vertex multiset and face-coordinate memberships.

    This helper intentionally ignores object names and object boundaries.  It is
    used only before/after temporary joins, where face topology must remain
    exactly unchanged.  GLB reimport may triangulate or duplicate material seams,
    so the external welded-union audit remains a separate later check.
    """
    vertices = []
    faces = []
    for obj in objects:
        if obj is None or obj.type != "MESH":
            continue
        world_coordinate = {
            vertex.index: tuple(
                round(float(value), precision)
                for value in (obj.matrix_world @ vertex.co)
            )
            for vertex in obj.data.vertices
        }
        vertices.extend(world_coordinate.values())
        faces.extend(
            tuple(sorted(world_coordinate[index] for index in polygon.vertices))
            for polygon in obj.data.polygons
        )
    payload = {
        "vertices": sorted(vertices),
        "faces": sorted(faces),
        "precision_decimal_places": precision,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _mesh_uv_loop_count(obj):
    """Return the total stored UV-loop values across every UV layer."""
    return sum(len(layer.data) for layer in obj.data.uv_layers)


def _mesh_material_names(obj):
    """Return stable non-empty material names referenced by one Mesh."""
    return {
        material.name
        for material in obj.data.materials
        if material is not None
    }


def _normalized_import_name(name, expected_names):
    """Remove only Blender's collision suffix when it restores an expected name."""
    normalized = re.sub(r"\.\d{3}$", "", name)
    return normalized if normalized in expected_names else name


def _normalized_material_name(name):
    """Normalize only the numeric suffix introduced by same-scene GLB reimport."""
    return re.sub(r"\.\d{3}$", "", name)


def export_prejoin_named_group_snapshot(
    asset_name,
    source_object_names,
    group_rules,
    group_representation,
    bake_component_world_transform,
    output_path,
    report_path,
):
    """Export exclusive construction owners from evaluated pre-join components.

    Input:
        asset_name          : Prefix used to derive each component suffix.
        source_object_names : Exact pre-join Mesh objects belonging to one
                              semantic owner.
        group_rules         : Git-text list containing group_id, name,
                              object_name and exclusive suffix_prefixes.
        group_representation: ``joined_meshes`` or
                              ``hierarchical_components``.
        bake_component_world_transform: Bake each evaluated copy to world
                              coordinates before GLB triangulation.
        output_path         : Diagnostic GLB destination.
        report_path         : Mechanical conservation report destination.
    Output:
        A report dictionary.  The production source objects are never modified;
        only evaluated temporary copies are joined and exported.
    """
    if not group_rules:
        raise RuntimeError("pre-join snapshot requires at least one group rule")
    if group_representation not in {
        "joined_meshes",
        "hierarchical_components",
    }:
        raise RuntimeError(
            "unsupported pre-join group representation: %s"
            % group_representation
        )
    group_ids = [int(rule["group_id"]) for rule in group_rules]
    group_names = [rule["name"] for rule in group_rules]
    group_object_names = [rule["object_name"] for rule in group_rules]
    if len(set(group_ids)) != len(group_ids):
        raise RuntimeError("pre-join snapshot group_id values must be unique")
    if len(set(group_names)) != len(group_names):
        raise RuntimeError("pre-join snapshot group names must be unique")
    if len(set(group_object_names)) != len(group_object_names):
        raise RuntimeError("pre-join snapshot object names must be unique")

    source_objects = []
    source_suffixes = {}
    assignments = {}
    coverage_errors = []
    for object_name in source_object_names:
        obj = bpy.data.objects.get(object_name)
        if obj is None or obj.type != "MESH":
            raise RuntimeError(
                "pre-join snapshot source is not a Mesh: %s" % object_name
            )
        suffix = (
            object_name[len(asset_name):]
            if object_name.startswith(asset_name)
            else object_name
        )
        matched_rules = [
            rule
            for rule in group_rules
            if any(
                suffix.startswith(prefix)
                for prefix in rule.get("suffix_prefixes", [])
            )
        ]
        if len(matched_rules) != 1:
            coverage_errors.append({
                "object": object_name,
                "suffix": suffix,
                "matched_groups": [rule["name"] for rule in matched_rules],
            })
            continue
        source_objects.append(obj)
        source_suffixes[object_name] = suffix
        assignments[object_name] = matched_rules[0]["name"]
    if coverage_errors:
        raise RuntimeError(
            "pre-join snapshot group coverage is not exclusive: %s"
            % json.dumps(coverage_errors, ensure_ascii=False)
        )
    if len(source_objects) != len(source_object_names):
        raise RuntimeError("pre-join snapshot did not retain every source object")

    saved_selection = list(bpy.context.selected_objects)
    saved_active = bpy.context.view_layer.objects.active
    depsgraph = bpy.context.evaluated_depsgraph_get()
    root = bpy.data.objects.new(asset_name + "_construction_snapshot_root", None)
    bpy.context.scene.collection.objects.link(root)
    temporary_copies = []
    grouped_copies = {rule["name"]: [] for rule in group_rules}
    created_groups = []
    component_expected_owner_names = {}
    group_records = []
    try:
        # Copy evaluated data before any temporary join.  This keeps modifiers,
        # materials and UV loops while leaving production objects untouched.
        for source in source_objects:
            evaluated = source.evaluated_get(depsgraph)
            mesh = bpy.data.meshes.new_from_object(
                evaluated,
                preserve_all_data_layers=True,
                depsgraph=depsgraph,
            )
            copy_name = source.name + "_construction_snapshot_copy"
            copy_obj = bpy.data.objects.new(copy_name, mesh)
            bpy.context.scene.collection.objects.link(copy_obj)
            if bake_component_world_transform:
                mesh.transform(evaluated.matrix_world)
                mesh.update()
                copy_obj.matrix_world = Matrix.Identity(4)
            else:
                copy_obj.matrix_world = evaluated.matrix_world.copy()
            temporary_copies.append(copy_obj)
            grouped_copies[assignments[source.name]].append(copy_obj)

        source_face_count = sum(
            len(obj.data.polygons) for obj in temporary_copies
        )
        source_vertex_count = sum(
            len(obj.data.vertices) for obj in temporary_copies
        )
        source_uv_loop_count = sum(
            _mesh_uv_loop_count(obj) for obj in temporary_copies
        )
        source_uv_layer_count = sum(
            len(obj.data.uv_layers) for obj in temporary_copies
        )
        source_material_names = sorted({
            name
            for obj in temporary_copies
            for name in _mesh_material_names(obj)
        })
        source_canonical_geometry_sha256 = _canonical_world_union_sha256(
            temporary_copies
        )

        for rule in sorted(group_rules, key=lambda item: int(item["group_id"])):
            group_name = rule["name"]
            copies = grouped_copies[group_name]
            if not copies:
                raise RuntimeError(
                    "pre-join snapshot group has no source objects: %s"
                    % group_name
                )
            component_names = sorted(
                source.name
                for source in source_objects
                if assignments[source.name] == group_name
            )
            component_suffixes = [
                source_suffixes[name] for name in component_names
            ]
            if group_representation == "joined_meshes":
                bpy.ops.object.select_all(action="DESELECT")
                for copy_obj in copies:
                    copy_obj.select_set(True)
                bpy.context.view_layer.objects.active = copies[0]
                bpy.ops.object.join()
                group_obj = copies[0]
                group_obj.name = rule["object_name"]
                group_obj.data.name = rule["object_name"] + "_mesh"
                world_matrix = group_obj.matrix_world.copy()
                group_obj.parent = root
                group_obj.matrix_world = world_matrix
                group_obj["construction_group_id"] = int(rule["group_id"])
                group_obj["construction_group_name"] = group_name
                created_groups.append(group_obj)
                partition_objects = [group_obj]
            else:
                group_obj = bpy.data.objects.new(rule["object_name"], None)
                bpy.context.scene.collection.objects.link(group_obj)
                group_obj.parent = root
                group_obj["construction_group_id"] = int(rule["group_id"])
                group_obj["construction_group_name"] = group_name
                created_groups.append(group_obj)
                for copy_obj in copies:
                    copy_obj.parent = group_obj
                    copy_obj["construction_group_id"] = int(rule["group_id"])
                    copy_obj["construction_group_name"] = group_name
                    component_expected_owner_names[copy_obj.name] = group_obj.name
                partition_objects = copies
            group_records.append({
                "group_id": int(rule["group_id"]),
                "name": group_name,
                "object": group_obj.name,
                "object_type": group_obj.type,
                "source_object_count": len(component_names),
                "source_objects": component_names,
                "source_suffixes": component_suffixes,
                "partition_object_count": len(partition_objects),
                "partition_objects": sorted(
                    obj.name for obj in partition_objects
                ),
                "partition_face_count": sum(
                    len(obj.data.polygons) for obj in partition_objects
                ),
                "partition_vertex_count": sum(
                    len(obj.data.vertices) for obj in partition_objects
                ),
                "partition_uv_layer_count": sum(
                    len(obj.data.uv_layers) for obj in partition_objects
                ),
                "partition_uv_loop_count": sum(
                    _mesh_uv_loop_count(obj) for obj in partition_objects
                ),
                "partition_material_names": sorted({
                    name
                    for obj in partition_objects
                    for name in _mesh_material_names(obj)
                }),
            })

        if group_representation == "joined_meshes":
            partition_objects = list(created_groups)
        else:
            partition_objects = list(temporary_copies)

        partition_face_count = sum(
            len(obj.data.polygons) for obj in partition_objects
        )
        partition_vertex_count = sum(
            len(obj.data.vertices) for obj in partition_objects
        )
        partition_uv_layer_count = sum(
            len(obj.data.uv_layers) for obj in partition_objects
        )
        partition_uv_loop_count = sum(
            _mesh_uv_loop_count(obj) for obj in partition_objects
        )
        partition_material_names = sorted({
            name
            for obj in partition_objects
            for name in _mesh_material_names(obj)
        })
        partition_canonical_geometry_sha256 = _canonical_world_union_sha256(
            partition_objects
        )

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        bpy.ops.object.select_all(action="DESELECT")
        root.select_set(True)
        for obj in created_groups:
            obj.select_set(True)
        for obj in partition_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = partition_objects[0]
        bpy.ops.export_scene.gltf(
            filepath=output_path,
            export_format="GLB",
            use_selection=True,
            export_apply=False,
            export_materials="EXPORT",
            export_texcoords=True,
            export_normals=True,
            export_tangents=True,
            export_extras=True,
            export_lights=False,
            export_cameras=False,
            export_animations=False,
        )

        before_import = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=output_path)
        imported = [obj for obj in bpy.data.objects if obj not in before_import]
        imported_meshes = [obj for obj in imported if obj.type == "MESH"]
        imported_empties = [obj for obj in imported if obj.type == "EMPTY"]
        imported_names = sorted(obj.name for obj in imported_meshes)
        expected_names = sorted(obj.name for obj in partition_objects)
        expected_name_set = set(expected_names)
        normalized_imported_names = sorted(
            _normalized_import_name(name, expected_name_set)
            for name in imported_names
        )
        expected_owner_names = sorted(
            rule["object_name"] for rule in group_rules
        )
        expected_owner_name_set = set(expected_owner_names)
        normalized_imported_owner_names = sorted({
            _normalized_import_name(obj.name, expected_owner_name_set)
            for obj in imported_empties
            if _normalized_import_name(
                obj.name, expected_owner_name_set
            ) in expected_owner_name_set
        })
        normalized_parent_by_component = {}
        for obj in imported_meshes:
            component_name = _normalized_import_name(
                obj.name, expected_name_set
            )
            parent_name = None
            if obj.parent is not None:
                parent_name = _normalized_import_name(
                    obj.parent.name, expected_owner_name_set
                )
            normalized_parent_by_component[component_name] = parent_name
        expected_parent_by_component = {
            component_name: owner_name
            for component_name, owner_name
            in sorted(component_expected_owner_names.items())
        }
        imported_material_names = sorted({
            _normalized_material_name(material.name)
            for obj in imported_meshes
            for material in obj.data.materials
            if material is not None
        })
        internal_conservation = {
            "face_count_equal": source_face_count == partition_face_count,
            "vertex_count_equal": source_vertex_count == partition_vertex_count,
            "uv_loop_count_equal": (
                source_uv_loop_count == partition_uv_loop_count
            ),
            "uv_layer_count_equal": (
                source_uv_layer_count == partition_uv_layer_count
            ),
            "material_names_equal": (
                source_material_names == partition_material_names
            ),
            "canonical_geometry_equal": (
                source_canonical_geometry_sha256
                == partition_canonical_geometry_sha256
            ),
        }
        report = {
            "schema": "bpy_prejoin_construction_subowner_snapshot/v1",
            "exporter_source": os.path.abspath(__file__),
            "exporter_source_sha256": _sha256(os.path.abspath(__file__)),
            "asset": asset_name,
            "group_representation": group_representation,
            "bake_component_world_transform": (
                bool(bake_component_world_transform)
            ),
            "source_object_count": len(source_objects),
            "source_objects": sorted(source.name for source in source_objects),
            "exclusive_assignment_count": len(assignments),
            "coverage_errors": coverage_errors,
            "source_face_count": source_face_count,
            "partition_face_count": partition_face_count,
            "source_vertex_count": source_vertex_count,
            "partition_vertex_count": partition_vertex_count,
            "source_uv_loop_count": source_uv_loop_count,
            "partition_uv_loop_count": partition_uv_loop_count,
            "source_uv_layer_count": source_uv_layer_count,
            "partition_uv_layer_count": partition_uv_layer_count,
            "source_material_names": source_material_names,
            "partition_material_names": partition_material_names,
            "source_canonical_world_union_geometry_sha256": (
                source_canonical_geometry_sha256
            ),
            "partition_canonical_world_union_geometry_sha256": (
                partition_canonical_geometry_sha256
            ),
            "groups": group_records,
            "internal_conservation": internal_conservation,
            "glb_path": output_path,
            "glb_bytes": os.path.getsize(output_path),
            "glb_sha256": _sha256(output_path),
            "reimport": {
                "mesh_count": len(imported_meshes),
                "expected_mesh_count": len(partition_objects),
                "object_names": imported_names,
                "expected_object_names": expected_names,
                "normalized_object_names": normalized_imported_names,
                "object_names_preserved": (
                    normalized_imported_names == expected_names
                ),
                "uv_layer_count": sum(
                    len(obj.data.uv_layers) for obj in imported_meshes
                ),
                "uv_loop_count": sum(
                    _mesh_uv_loop_count(obj) for obj in imported_meshes
                ),
                "construction_owner_count": len(
                    normalized_imported_owner_names
                ),
                "expected_construction_owner_count": len(group_rules),
                "normalized_construction_owner_names": (
                    normalized_imported_owner_names
                ),
                "expected_construction_owner_names": expected_owner_names,
                "construction_owner_names_preserved": (
                    normalized_imported_owner_names == expected_owner_names
                    if group_representation == "hierarchical_components"
                    else True
                ),
                "component_parent_owners": normalized_parent_by_component,
                "expected_component_parent_owners": (
                    expected_parent_by_component
                ),
                "component_parent_owners_preserved": (
                    normalized_parent_by_component
                    == expected_parent_by_component
                    if group_representation == "hierarchical_components"
                    else True
                ),
                "normalized_material_names": imported_material_names,
                "material_names_preserved": (
                    imported_material_names == source_material_names
                ),
            },
            "external_union_geometry_audit_pending": True,
            "direct_multiview_review_pending": True,
            "deterministic_second_build_pending": True,
            "quality_claim": False,
        }
        report["passed"] = (
            not report["coverage_errors"]
            and report["exclusive_assignment_count"]
            == report["source_object_count"]
            and all(internal_conservation.values())
            and report["reimport"]["mesh_count"]
            == report["reimport"]["expected_mesh_count"]
            and report["reimport"]["object_names_preserved"]
            and report["reimport"]["construction_owner_names_preserved"]
            and report["reimport"]["component_parent_owners_preserved"]
            and report["reimport"]["material_names_preserved"]
            and report["reimport"]["uv_layer_count"]
            == report["partition_uv_layer_count"]
        )
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)

        for obj in imported:
            bpy.data.objects.remove(obj, do_unlink=True)
        return report
    finally:
        # Joined temporary copies that remain in the scene are exactly the
        # created group objects.  Remove them and any failed pre-join copies,
        # then restore the production selection without touching source data.
        cleanup_objects = list(created_groups) + list(temporary_copies)
        seen = set()
        for obj in cleanup_objects:
            if obj is None or id(obj) in seen:
                continue
            seen.add(id(obj))
            try:
                object_name = obj.name
            except ReferenceError:
                # ``bpy.ops.object.join`` already removed this temporary copy.
                continue
            if object_name in bpy.data.objects:
                mesh = obj.data
                bpy.data.objects.remove(obj, do_unlink=True)
                if mesh is not None and mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
        if root.name in bpy.data.objects:
            bpy.data.objects.remove(root, do_unlink=True)
        bpy.ops.object.select_all(action="DESELECT")
        for obj in saved_selection:
            if obj.name in bpy.data.objects:
                obj.select_set(True)
        if saved_active is not None and saved_active.name in bpy.data.objects:
            bpy.context.view_layer.objects.active = saved_active


def export_semantic_part_snapshot(
    asset_name,
    attribute_name,
    id_to_name,
    output_path,
    report_path,
):
    """Partition ``asset_name`` by a FACE INT attribute and export one GLB."""
    source = bpy.data.objects.get(asset_name)
    if source is None or source.type != "MESH":
        raise RuntimeError("semantic snapshot source is not a Mesh: %s" % asset_name)
    attribute = source.data.attributes.get(attribute_name)
    if attribute is None or attribute.domain != "FACE" or attribute.data_type != "INT":
        raise RuntimeError(
            "semantic snapshot requires FACE INT attribute %s on %s"
            % (attribute_name, asset_name)
        )

    grouped_polygons = {}
    for polygon in source.data.polygons:
        owner_id = int(attribute.data[polygon.index].value)
        grouped_polygons.setdefault(owner_id, []).append(polygon.index)

    saved_selection = list(bpy.context.selected_objects)
    saved_active = bpy.context.view_layer.objects.active
    root = bpy.data.objects.new(asset_name + "_semantic_snapshot_root", None)
    bpy.context.scene.collection.objects.link(root)
    created = []
    part_records = []
    try:
        for owner_id in sorted(grouped_polygons):
            semantic_name = id_to_name.get(owner_id, "unknown_%03d" % owner_id)
            # ``owner_id`` is an asset-local semantic code, not the contract's
            # P-number.  Use an unambiguous namespace so evidence cannot map a
            # raw ID to the wrong contract part.
            object_name = "SEM%03d_%s_source" % (owner_id, semantic_name)
            mesh = _subset_mesh(
                source,
                grouped_polygons[owner_id],
                object_name + "_mesh",
            )
            obj = bpy.data.objects.new(object_name, mesh)
            bpy.context.scene.collection.objects.link(obj)
            world_matrix = source.matrix_world.copy()
            obj.parent = root
            obj.matrix_world = world_matrix
            obj["semantic_part_id"] = owner_id
            obj["semantic_part_name"] = semantic_name
            created.append(obj)
            part_records.append({
                "owner_id": owner_id,
                "semantic_name": semantic_name,
                "object": object_name,
                "source_face_count": len(grouped_polygons[owner_id]),
                "source_vertex_count": len(mesh.vertices),
                "uv_layer_count": len(mesh.uv_layers),
                "material_count": len([item for item in mesh.materials if item]),
            })

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        bpy.ops.object.select_all(action="DESELECT")
        root.select_set(True)
        for obj in created:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = created[0]
        bpy.ops.export_scene.gltf(
            filepath=output_path,
            export_format="GLB",
            use_selection=True,
            export_apply=False,
            export_materials="EXPORT",
            export_texcoords=True,
            export_normals=True,
            export_tangents=True,
            export_extras=True,
            export_lights=False,
            export_cameras=False,
            export_animations=False,
        )

        before_import = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=output_path)
        imported = [obj for obj in bpy.data.objects if obj not in before_import]
        imported_meshes = [obj for obj in imported if obj.type == "MESH"]
        imported_names = sorted(obj.name for obj in imported_meshes)
        expected_names = sorted(obj.name for obj in created)
        normalized_imported_names = sorted(
            re.sub(r"\.\d{3}$", "", name) if re.sub(r"\.\d{3}$", "", name) in expected_names else name
            for name in imported_names
        )
        report = {
            "schema": "bpy_semantic_part_snapshot/v1",
            "exporter_source": os.path.abspath(__file__),
            "exporter_source_sha256": _sha256(os.path.abspath(__file__)),
            "asset": asset_name,
            "attribute": attribute_name,
            "source_face_count": len(source.data.polygons),
            "partition_face_count": sum(item["source_face_count"] for item in part_records),
            "source_owner_count": len(part_records),
            "parts": part_records,
            "glb_path": output_path,
            "glb_bytes": os.path.getsize(output_path),
            "glb_sha256": _sha256(output_path),
            "reimport": {
                "mesh_count": len(imported_meshes),
                "expected_mesh_count": len(created),
                "object_names": imported_names,
                "expected_object_names": expected_names,
                "object_names_strict_preserved": imported_names == expected_names,
                "normalized_object_names": normalized_imported_names,
                "object_names_preserved": normalized_imported_names == expected_names,
                "uv_layer_count": sum(len(obj.data.uv_layers) for obj in imported_meshes),
                "material_names": sorted({
                    material.name
                    for obj in imported_meshes
                    for material in obj.data.materials
                    if material is not None
                }),
            },
        }
        report["passed"] = (
            report["partition_face_count"] == report["source_face_count"]
            and report["reimport"]["mesh_count"] == report["reimport"]["expected_mesh_count"]
            and report["reimport"]["object_names_preserved"]
            and report["reimport"]["uv_layer_count"] >= len(created)
        )
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)

        for obj in imported:
            bpy.data.objects.remove(obj, do_unlink=True)
        return report
    finally:
        for obj in created:
            if obj.name in bpy.data.objects:
                mesh = obj.data
                bpy.data.objects.remove(obj, do_unlink=True)
                if mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
        if root.name in bpy.data.objects:
            bpy.data.objects.remove(root, do_unlink=True)
        bpy.ops.object.select_all(action="DESELECT")
        for obj in saved_selection:
            if obj.name in bpy.data.objects:
                obj.select_set(True)
        if saved_active is not None and saved_active.name in bpy.data.objects:
            bpy.context.view_layer.objects.active = saved_active
