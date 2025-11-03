# Main Code
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
# Reload Files
common_top._auto_reload_modules([mm_cm_lib, mdl_cm_lib, mtal_cm_lib, ani_cm_lib, common_top])
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
# 環境初期化
override_common = mm_cm_lib.bpy_modeling_initialize_common(
    reload_list=[
        glb
    ,   wrap
    ,   d00_mdl
    ,   d01_uv_unwrap
    ,   d02_mtal
    ,   d03_bake
    ,   d04_bone
    ,   d05_animation
    ,   d06_shape_key
    ,   model
    ,   material
    ]               # Reload Dir/File
,   rm_flg=False    # Object Delete Disable
)

# ==================================================================
# = ▼ Instance
# ==================================================================

# --------------------------------
# Base Light 作成 & 配置
# --------------------------------
if (glb.glb.glb_exist_obj_chk(obj_list=[glb.glb.base_light], gen_flag=True)):
    # ポイントライト追加
    bpy.ops.object.light_add(
        type='POINT'
    ,   radius=1
    ,   align='WORLD'
    ,   location=(-3, -3, 3)
    ,   scale=(1, 1, 1)
    )
    # 名前設定
    bpy.context.object.name = glb.glb.base_light
    # パワー変更
    bpy.context.object.data.energy = 50000
    # 半径設定
    bpy.context.object.data.shadow_soft_size = 10

# アクティブオブジェクト
mdl_cm_lib.active_object_select(
    object_name_list=[glb.glb.base_light]
)

# --------------------------------
# sample_obj 作成 & 配置
# --------------------------------
object_list=[
    glb.glb.sukima_logo
,   glb.glb.sukima_logo_bone
]
# オブジェクト作成
if (mm_cm_lib.require_new_objects(obj_list=object_list, rm_flag=False)):
    wrap.sukima_logo_wrap.sukima_logo_wrap()
# コレクション作成+格納
mm_cm_lib.collection_create_or_move(
    object_list=object_list
,   collection_name="LOGO_OBJ"
,   move_to_collection_name="NaN"
)

print(glb.glb.EXIST_FLAG_DICT)