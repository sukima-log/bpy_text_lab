# Sub Code
import bpy, os, sys, subprocess
# Get File Path
script_path = bpy.path.abspath(bpy.context.space_data.text.filepath)
script_dir = os.path.dirname(script_path)
# Get Git Root
git_root = subprocess.run(
    ["git", "-C", script_dir, "rev-parse", "--show-toplevel"],
    stdout=subprocess.PIPE, text=True
).stdout.strip()
# Add the parent directory of the root to sys.path
if git_root and git_root not in sys.path:
    sys.path.append(git_root)
# Common Setting
import Common.common_top as common_top
from Common.common_top import *
#========================================================================================
# ==================================================================
# = Pre Process
# ==================================================================
modules = cm_lib.import_submodules(f"Assets.mdl.SAMPLE_MODEL") 
parts = cm_lib.import_submodules("Assets.parts")

globals().update(modules)

# =====================================================
# Bake
# =====================================================
def sukima_logo_bake(
    obj_name
):
    if (mm_cm_lib.glb_exist_obj_chk(obj_list=[obj_name], EXIST_FLAG_DICT=glb.glb_defs.EXIST_FLAG_DICT, gen_flag=False)):
        obj_name=obj_name
        # ビューへ切り替え
        mdl_cm_lib.change_preview(key="MATERIAL")
        # Mode切り替え
        bpy.ops.object.mode_set(mode='OBJECT')
        # アクティブオブジェクト
        mdl_cm_lib.active_object_select(object_name_list=[obj_name])

        # Mode切り替え
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        # ------------------------------------
        # Bake
        # ------------------------------------
        mtal_list=[
            glb.glb_defs.MT_SUKIMA_LOGO_BASE
        ,   glb.glb_defs.MT_SUKIMA_LOGO_BLACK
        ,   glb.glb_defs.MT_SUKIMA_LOGO_ORANGE
        ,   glb.glb_defs.MT_SUKIMA_LOGO_GRAY
        ,   glb.glb_defs.MT_SUKIMA_LOGO_LIGHT_GREEN
        ,   glb.glb_defs.MT_SUKIMA_LOGO_GREEN
        ]
        bk_list=[
            "DIFFUSE"
        ,   "ROUGHNESS"
        ,   "NORMAL"
        ]
        for i in range(len(bk_list)):
            # ------------------------------------
            # ベイク用テクスチャ画像作成
            # ------------------------------------
            bake_image_name = "bk_img_" + obj_name + "_" + bk_list[i]
            mtal_cm_lib.create_bake_texture_image(
                image_name=bake_image_name
            ,   width=2048
            ,   height=2048
            ,   color=(0.0, 0.0, 0.0, 1.0)
            ,   alpha=True
            )
            mtal_cm_lib.bake_image_save(
                obj_name=obj_name
            ,   bake_image_name=bake_image_name
            ,   bake_type=bk_list[i]
            ,   image_path=script_dir + "/bake_texture/" + obj_name + "/" + obj_name + "_" + bk_list[i] + ".png"
            ,   file_format="PNG"
            ,   margin=16
            ,   samples=256
            ,   material_list=mtal_list
            ,   node_locate=i
            )





