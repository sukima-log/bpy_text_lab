bl_info = {
    "name": "Persistent ID Overlay (VID/EID/PID) - Blender5 Fix",
    "author": "ChatGPT",
    "version": (1, 3),
    "blender": (5, 1, 0),
    "location": "View3D > N Panel > CustomID",
    "description": "Show vertex/edge/face persistent IDs (vid/eid/fid) in 3D view. Selection-only, color and size options. Blender5 safe.",
    "category": "3D View",
}

import bpy
import bmesh
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from bpy_extras import view3d_utils

_draw_handler = None
_font_id = 0

# --------------------
# Helpers
# --------------------
def iter_view3d_regions():
    """Yield (window, area, region, space) for each VIEW_3D WINDOW region."""
    wm = bpy.context.window_manager
    for window in wm.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                for region in area.regions:
                    if region.type == 'WINDOW':
                        yield window, area, region, space

def world_to_region_2d(region, rv3d, coord):
    if rv3d is None:
        return None
    try:
        return view3d_utils.location_3d_to_region_2d(region, rv3d, coord)
    except Exception:
        return None

def ensure_attrs_exist(mesh):
    return {
        "vid": ("vid" in mesh.attributes),
        "eid": ("eid" in mesh.attributes),
        "fid": ("fid" in mesh.attributes),
    }

# --------------------
# Draw handler
# --------------------
def draw_persistent_ids():
    context = bpy.context
    if context.mode != 'EDIT_MESH':
        return

    scene = context.scene
    font_size = getattr(scene, "persistent_id_overlay_font_size", 12)
    show_only_selected = getattr(scene, "persistent_id_overlay_show_only_selected", False)
    col_vid = getattr(scene, "persistent_id_overlay_color_vid", (0.6, 1.0, 0.3, 1.0))
    col_eid = getattr(scene, "persistent_id_overlay_color_eid", (0.6, 1.0, 0.3, 1.0))
    col_fid = getattr(scene, "persistent_id_overlay_color_fid", (0.6, 1.0, 0.3, 1.0))

    blf.size(_font_id, font_size)

    # Iterate over 3D View areas
    for _win, area, region, space in iter_view3d_regions():
        rv3d = getattr(space, "region_3d", None)
        obj = bpy.context.edit_object
        if obj is None or obj.type != 'MESH':
            continue
        me = obj.data
        attrs = ensure_attrs_exist(me)
        if not any(attrs.values()):
            # draw hint in top-left corner
            pos_x = region.x + 8
            pos_y = region.y + region.height - 20
            blf.position(_font_id, pos_x, pos_y, 0)
            blf.color(_font_id, 1.0, 0.3, 0.3, 1.0)
            blf.draw(_font_id, "No vid/eid/fid attributes")
            continue

        try:
            bm = bmesh.from_edit_mesh(me)
        except Exception:
            continue

        layer_vid = bm.verts.layers.int.get("vid") if attrs["vid"] else None
        layer_eid = bm.edges.layers.int.get("eid") if attrs["eid"] else None
        layer_fid = bm.faces.layers.int.get("fid") if attrs["fid"] else None
        mat_world = obj.matrix_world

        sel_vert, sel_edge, sel_face = context.tool_settings.mesh_select_mode

        # Draw Faces (PID)
        if sel_face and layer_fid:
            for f in bm.faces:
                if show_only_selected and not f.select:
                    continue
                center = sum((v.co for v in f.verts), Vector()) / len(f.verts)
                wp = mat_world @ center
                screen = world_to_region_2d(region, rv3d, wp)
                if screen:
                    blf.position(_font_id, screen.x, screen.y, 0)
                    blf.color(_font_id, *col_fid)
                    blf.draw(_font_id, str(f[layer_fid]))

        # Draw Edges (EID)
        if sel_edge and layer_eid:
            for e in bm.edges:
                if show_only_selected and not e.select:
                    continue
                mid = (e.verts[0].co + e.verts[1].co) * 0.5
                wp = mat_world @ mid
                screen = world_to_region_2d(region, rv3d, wp)
                if screen:
                    blf.position(_font_id, screen.x, screen.y, 0)
                    blf.color(_font_id, *col_eid)
                    blf.draw(_font_id, str(e[layer_eid]))

        # Draw Vertices (VID)
        if sel_vert and layer_vid:
            for v in bm.verts:
                if show_only_selected and not v.select:
                    continue
                wp = mat_world @ v.co
                screen = world_to_region_2d(region, rv3d, wp)
                if screen:
                    blf.position(_font_id, screen.x, screen.y, 0)
                    blf.color(_font_id, *col_vid)
                    blf.draw(_font_id, str(v[layer_vid]))

# --------------------
# Operators / Panel
# --------------------
class PERSISTENTID_OT_overlay_enable(bpy.types.Operator):
    bl_idname = "view3d.persistent_id_overlay_enable"
    bl_label = "Enable VID/EID/PID Overlay"

    def execute(self, context):
        global _draw_handler
        if _draw_handler is None:
            _draw_handler = bpy.types.SpaceView3D.draw_handler_add(draw_persistent_ids, (), 'WINDOW', 'POST_PIXEL')

        for _w, area, _r, _s in iter_view3d_regions():
            area.tag_redraw()

        self.report({'INFO'}, "Persistent ID Overlay: Enabled")
        return {'FINISHED'}

class PERSISTENTID_OT_overlay_disable(bpy.types.Operator):
    bl_idname = "view3d.persistent_id_overlay_disable"
    bl_label = "Disable VID/EID/PID Overlay"

    def execute(self, context):
        global _draw_handler
        if _draw_handler is not None:
            bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, 'WINDOW')
            _draw_handler = None

        for _w, area, _r, _s in iter_view3d_regions():
            area.tag_redraw()

        self.report({'INFO'}, "Persistent ID Overlay: Disabled")
        return {'FINISHED'}

class PERSISTENTID_PT_panel(bpy.types.Panel):
    bl_label = "Persistent ID Overlay"
    bl_category = "CustomID"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("view3d.persistent_id_overlay_enable")
        row.operator("view3d.persistent_id_overlay_disable")
        layout.prop(context.scene, 'persistent_id_overlay_font_size')
        layout.prop(context.scene, 'persistent_id_overlay_show_only_selected')
        layout.prop(context.scene, 'persistent_id_overlay_color_vid')
        layout.prop(context.scene, 'persistent_id_overlay_color_eid')
        layout.prop(context.scene, 'persistent_id_overlay_color_fid')

# --------------------
# Scene Props
# --------------------
def register_scene_props():
    bpy.types.Scene.persistent_id_overlay_font_size = bpy.props.IntProperty(
        name="Font Size", default=12, min=6, max=48)
    bpy.types.Scene.persistent_id_overlay_show_only_selected = bpy.props.BoolProperty(
        name="Show only selected", default=False)
    bpy.types.Scene.persistent_id_overlay_color_vid = bpy.props.FloatVectorProperty(
        name="VID Color", subtype='COLOR', size=4, default=(0.6, 1.0, 0.3, 1.0))
    bpy.types.Scene.persistent_id_overlay_color_eid = bpy.props.FloatVectorProperty(
        name="EID Color", subtype='COLOR', size=4, default=(0.6, 1.0, 0.3, 1.0))
    bpy.types.Scene.persistent_id_overlay_color_fid = bpy.props.FloatVectorProperty(
        name="PID Color", subtype='COLOR', size=4, default=(0.6, 1.0, 0.3, 1.0))

def unregister_scene_props():
    for prop in [
        "persistent_id_overlay_font_size",
        "persistent_id_overlay_show_only_selected",
        "persistent_id_overlay_color_vid",
        "persistent_id_overlay_color_eid",
        "persistent_id_overlay_color_fid"]:
        try:
            delattr(bpy.types.Scene, prop)
        except Exception:
            pass

# --------------------
# Registration
# --------------------
classes = (
    PERSISTENTID_OT_overlay_enable,
    PERSISTENTID_OT_overlay_disable,
    PERSISTENTID_PT_panel,
)

def register():
    for c in classes: bpy.utils.register_class(c)
    register_scene_props()

def unregister():
    global _draw_handler
    if _draw_handler: bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, 'WINDOW')
    _draw_handler = None
    for c in classes: bpy.utils.unregister_class(c)
    unregister_scene_props()

if __name__ == "__main__":
    register()
