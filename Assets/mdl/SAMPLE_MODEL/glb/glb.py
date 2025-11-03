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
#------------------------------------------------
# Exist Flag
#------------------------------------------------
# [[obj_name1, obj_name2, ...], True/False] のリスト形式
#  True: 全て存在, False: 存在しないものがある
# グローバル存在フラグ辞書
EXIST_FLAG_DICT = {}

def reset_exist_flag_dict():
    EXIST_FLAG_DICT.clear()  # 中身だけ空にする


#------------------------------------------------
# Global Parameter
#------------------------------------------------
GP_CUBE_SIZE    = 0.3   # 30 cm * 30 cm * 30 cm

#------------------------------------------------
# Objects
#------------------------------------------------
# Sample Light
base_light      = "base_light"
# Create Object
sukima_logo     = "sukima_logo"
# Armature
sukima_logo_bone    = "sukima_logo_bone"

#------------------------------------------------
# Material
#------------------------------------------------
# sukima_logo
MT_SUKIMA_LOGO_BASE         = "MT_SUKIMA_LOGO_BASE"
MT_SUKIMA_LOGO_BLACK        = "MT_SUKIMA_LOGO_BLACK"
MT_SUKIMA_LOGO_ORANGE       = "MT_SUKIMA_LOGO_ORANGE"
MT_SUKIMA_LOGO_GRAY         = "MT_SUKIMA_LOGO_GRAY"
MT_SUKIMA_LOGO_LIGHT_GREEN  = "MT_SUKIMA_LOGO_LIGHT_GREEN"
MT_SUKIMA_LOGO_GREEN        = "MT_SUKIMA_LOGO_GREEN"
#------------------------------------------------
# Animation/Action
#------------------------------------------------
# sukima_logo
ANI_SUKIMA_LOGO_BONE_RUN    = "ANI_SUKIMA_LOGO_BONE_RUN"

#------------------------------------------------
# Object Existence Check
#------------------------------------------------
def glb_exist_obj_chk(obj_list=["object_name"], gen_flag=False):
    """
    Blender内のオブジェクト + ボーン存在確認 + 必要に応じ全削除 / 辞書管理
    - obj_list のどれか1つでも存在しなければ obj_list 内全削除
    - gen_flag に応じて辞書の参照/更新
    """

    global EXIST_FLAG_DICT

    # --- ヘルパー関数 ---
    def object_exists(name):
        """オブジェクト（メッシュ/Empty/アーマチュア）が存在するか"""
        return bpy.data.objects.get(name) is not None

    def bone_exists(name):
        """ボーンが存在するか（すべてのアーマチュアを探索）"""
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE' and obj.data.bones.get(name):
                return True
        return False

    def delete_object_or_bone(name):
        """オブジェクトまたはボーンを削除"""
        obj = bpy.data.objects.get(name)
        if obj:
            # 子オブジェクトも再帰削除
            for child in obj.children[:]:
                delete_object_or_bone(child.name)
            bpy.data.objects.remove(obj, do_unlink=True)
        else:
            # ボーン削除（アーマチュア内）
            for arm in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
                if name in arm.data.bones:
                    # ボーン削除には編集モード切替が必要
                    bpy.context.view_layer.objects.active = arm
                    bpy.ops.object.mode_set(mode='EDIT')
                    eb = arm.data.edit_bones.get(name)
                    if eb:
                        arm.data.edit_bones.remove(eb)
                    bpy.ops.object.mode_set(mode='OBJECT')

    # --- 存在チェック ---
    exist_flags = []
    for name in obj_list:
        if object_exists(name):
            exist_flags.append(True)
        elif bone_exists(name):
            exist_flags.append(True)
        else:
            exist_flags.append(False)

    # --- gen_flag = True の場合 ---
    if gen_flag:
        # obj_list の全部分集合を辞書登録
        for r in range(1, len(obj_list) + 1):
            for combo in combinations(obj_list, r):
                EXIST_FLAG_DICT[combo] = all(
                    (object_exists(n) or bone_exists(n)) for n in combo
                )

        # どれか1つでも存在しなければ True（生成フラグ）
        if not all(exist_flags):
            # 存在しない場合、obj_list 全削除
            for name in obj_list:
                delete_object_or_bone(name)
            return True
        else:
            return False

    # --- gen_flag = False の場合 ---
    else:
        key = tuple(obj_list)
        if key in EXIST_FLAG_DICT:
            if EXIST_FLAG_DICT[key]:
                return False  # すでに存在していた
            else:
                return True   # 再生成されたので編集対象
        else:
            return True





