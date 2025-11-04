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
from Common.common_top import *
#========================================================================================
# ==================================================================
# = Pre Process
# ==================================================================
from Assets.mdl.SAMPLE_MODEL import (
    glb, wrap, d00_mdl, d01_uv_unwrap, d02_mtal, d03_bake, d04_bone, d05_animation, d06_shape_key
)
from Assets.parts import (
    model, material
)
# =====================================================
# Material
# =====================================================
def sukima_logo_mtal(
    sukima_logo=glb.glb.sukima_logo
):
    if (mm_cm_lib.glb_exist_obj_chk(obj_list=[sukima_logo], EXIST_FLAG_DICT=glb.glb.EXIST_FLAG_DICT, gen_flag=False)):
        obj_name=sukima_logo
        # ビューへ切り替え
        mdl_cm_lib.change_preview(key="MATERIAL")
        # Mode切り替え
        bpy.ops.object.mode_set(mode='OBJECT')
        # アクティブオブジェクト
        mdl_cm_lib.active_object_select(object_name_list=[obj_name])

        # マテリアル 金属
        # material.metal_mtal.mtal_metal_00(mtal_name=glb.glb.MT_SUKIMA_LOGO_BLACK)
        # material.metal_mtal.mtal_metal_00(mtal_name=glb.glb.MT_SUKIMA_LOGO_ORANGE)
        # material.metal_mtal.mtal_metal_00(mtal_name=glb.glb.MT_SUKIMA_LOGO_GRAY)
        # material.metal_mtal.mtal_metal_00(mtal_name=glb.glb.MT_SUKIMA_LOGO_LIGHT_GREEN)
        # material.metal_mtal.mtal_metal_00(mtal_name=glb.glb.MT_SUKIMA_LOGO_GREEN)

        # マテリアル 木素材
        material.wood_mtal.mtal_wood_01(
            mtal_name=glb.glb.MT_SUKIMA_LOGO_BLACK
        ,   Color_Ramp_00_color_1=mtal_cm_lib.hex_to_rgba(hex_color="#000000", alpha=1.0)
        ,   Color_Ramp_00_color_0=mtal_cm_lib.hex_to_rgba(hex_color="#000000", alpha=1.0)
        )
        material.wood_mtal.mtal_wood_01(
            mtal_name=glb.glb.MT_SUKIMA_LOGO_ORANGE
        ,   Color_Ramp_00_color_1=mtal_cm_lib.hex_to_rgba(hex_color="#ed5b00", alpha=1.0)
        ,   Color_Ramp_00_color_0=mtal_cm_lib.hex_to_rgba(hex_color="#d67f0e", alpha=1.0)
        )
        material.wood_mtal.mtal_wood_01(
            mtal_name=glb.glb.MT_SUKIMA_LOGO_GRAY
        ,   Color_Ramp_00_color_1=mtal_cm_lib.hex_to_rgba(hex_color="#919191", alpha=1.0)
        ,   Color_Ramp_00_color_0=mtal_cm_lib.hex_to_rgba(hex_color="#636363", alpha=1.0)
        )
        material.wood_mtal.mtal_wood_01(
            mtal_name=glb.glb.MT_SUKIMA_LOGO_LIGHT_GREEN
        ,   Color_Ramp_00_color_1=mtal_cm_lib.hex_to_rgba(hex_color="#50d875", alpha=1.0)
        ,   Color_Ramp_00_color_0=mtal_cm_lib.hex_to_rgba(hex_color="#2ca813", alpha=1.0)
        )
        material.wood_mtal.mtal_wood_01(
            mtal_name=glb.glb.MT_SUKIMA_LOGO_GREEN
        ,   Color_Ramp_00_color_1=mtal_cm_lib.hex_to_rgba(hex_color="#199f93", alpha=1.0)
        ,   Color_Ramp_00_color_0=mtal_cm_lib.hex_to_rgba(hex_color="#3bd393", alpha=1.0)
        )

        



