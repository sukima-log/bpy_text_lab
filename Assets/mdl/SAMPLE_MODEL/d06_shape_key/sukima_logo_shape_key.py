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
    sukima_logo=glb.glb_defs.sukima_logo
):
    if (mm_cm_lib.glb_exist_obj_chk(obj_list=[sukima_logo], EXIST_FLAG_DICT=glb.glb_defs.EXIST_FLAG_DICT, gen_flag=False)):
        obj_name=sukima_logo
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
        # アクティブ
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
        while bpy.context.object.active_shape_key_index > 0:
            bpy.ops.object.shape_key_move(type='UP')
        # Mode切り替え
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='EDGE')
        i_array=[815    ,816    ,832    ,839    ,850    ,870    ,877    ,884    ,890    ,899    ,909    ,911    ,920    ,922    ,931    ,933    ,936    ,939    ,943    ,946    ,948    ,1025   ,1057   ,1058   ,1071   ,1080   ,1081   ,1099   ,1106   ,1115   ,1119   ,1122   ,1131   ,1140   ,1160   ,1169   ,1181   ,1185   ,1251   ,1261   ,1265   ,1269   ,1275   ,1277   ,1281   ,1382   ,1388   ,1406   ,1415   ,1469   ,1476   ,1488   ,1490   ,1496   ,1497   ,1510   ,1515   ,1526   ,1530   ,1554   ,1560]
        x_array=[+0.0000,+0.0000,+0.0000,-0.0444,+0.0000,+0.0000,+0.0000,+0.0000,-0.0444,-0.0444,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,-0.0444,-0.0444,-0.0444,-0.0444,-0.0444,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0733,+0.0733,+0.0733,+0.0733,+0.0733,+0.0733,+0.0733,+0.0733,+0.0482,+0.0482,+0.0482,+0.0482]
        y_array=[+0.0000,+0.0000,+0.0475,+0.0000,+0.0475,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0475,+0.0475,+0.0475,+0.0475,+0.0475,+0.0475,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,-0.0276,-0.0276,-0.0276,-0.0276,-0.0276,-0.0276,-0.0276,-0.0276,-0.0276,-0.0276,-0.0276,-0.0276,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0475,+0.0475,+0.0475,+0.0475,+0.0475,+0.0475,+0.0475,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000]
        z_array=[+0.0579,+0.0579,+0.0000,+0.0000,+0.0000,+0.0579,+0.0579,+0.0579,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0579,+0.0579,+0.0579,+0.0579,+0.0579,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,-0.0165,-0.0165,-0.0165,-0.0165,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000,+0.0000]
        for i in range(len(i_array)):
            # 要素選択
            mdl_cm_lib.element_select(
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


