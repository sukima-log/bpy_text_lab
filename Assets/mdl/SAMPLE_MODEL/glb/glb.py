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



