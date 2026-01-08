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

# ==================================================================
# = Shape Key
# ==================================================================
def sukima_logo_shape_key(
    obj_name
):
    if (mm_cm_lib.glb_exist_obj_chk(obj_list=[obj_name], EXIST_FLAG_DICT=glb.glb_defs.EXIST_FLAG_DICT, gen_flag=False)):
        obj_name=obj_name
        # Mode切り替え
        bpy.ops.object.mode_set(mode='OBJECT')
        # アクティブオブジェクト
        ani_cm_lib.active_object_select_ext(
            object_name_list=[obj_name]
        )
        # --------------------------------
        # Basis (ベース作成)
        # --------------------------------
        # シェープキー追加
        bpy.ops.object.shape_key_add(from_mix=False)
        # # アクティブ
        bpy.context.object.active_shape_key_index = 0
        # 名前変更
        bpy.context.object.active_shape_key.name = "Basis"
        # --------------------------------
        # Shape Key 追加
        # --------------------------------
        # シェープキー追加
        bpy.ops.object.shape_key_add(from_mix=False)
        # アクティブ
        bpy.context.object.active_shape_key_index = 1
        # 名前変更
        bpy.context.object.active_shape_key.name = "Key_1"
        # --------------------------------
        # Shape Key 変形
        # --------------------------------
        # アクティブ
        bpy.context.object.active_shape_key_index = 1
        # リスト移動
        obj = bpy.context.object
        ani_cm_lib.move_shape_key_up_safe(
            obj=obj,
            shape_key_name="Key_1"
        )
        # Mode切り替え
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='EDGE')
        i_array=[1210,1234,1426,1942,2038,2098,2194,2290,2734,2770,2818,2854,2878,4006,4018,4258,4270,4438,4474,4618,4678,4762,4810,5614,5710,5746,6322,6382,6634,6910,7138,7198,7462,7510,7522,7570,7690,7774,7798,7882,8350,8554,8842,8986]
        x_array=[+0.0000,+0.0000,-0.0395,+0.0000,+0.0000,+0.0000,-0.0395,-0.0395,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,-0.0395,-0.0395,-0.0395,-0.0395,-0.0395,+0.0736,+0.0736,+0.0736,+0.0736,+0.0736,+0.0736,+0.0736,+0.0736,+0.0736,+0.0736,+0.0736,+0.0736,+0.0000,+0.0000,+0.0000,+0.0000]
        y_array=[+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,-0.0426,-0.0426,-0.0426,-0.0426,-0.0426,-0.0426,-0.0426,-0.0426,-0.0426,-0.0426,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0376,+0.0376,+0.0376,+0.0376]
        z_array=[+0.0423,+0.0423,+0.0000,+0.0423,+0.0423,+0.0423,+0.0000,+0.0000,+0.0423,+0.0423,+0.0423,+0.0423,+0.0423,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000]
        for i in range(len(i_array)):
            # 要素選択
            mdl_cm_lib.element_select_customid(
                element_list=[i_array[i]]
            ,   select_mode="VERT"
            ,   object_name_list=[obj_name]
            )
            # オブジェクト移動
            bpy.ops.transform.translate(
                value=(x_array[i], y_array[i], z_array[i])
            ,   orient_type='GLOBAL'
            )
        # Mode切り替え
        bpy.ops.object.mode_set(mode='OBJECT')
        # リスト移動
        bpy.ops.object.shape_key_move(type='DOWN')
        # アクティブ
        bpy.context.object.active_shape_key_index = 1
        # Shape Key 確認
        bpy.context.object.active_shape_key.value = 0.0 # (0.0 ~ 1.0)
        # アクティブ
        bpy.context.object.active_shape_key_index = 0


