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
# = Wrap Modules
# ==================================================================
# --------------------------------
# SAMPLE 作成 & 配置
# --------------------------------
def sukima_logo_wrap(
):
    # --------------------------------
    # Create Model (メッシュ)
    # --------------------------------
    d00_mdl.sukima_logo_mdl.sukima_logo_mdl()
    # --------------------------------
    # UV_unwrap (シーム, UV展開)
    # --------------------------------
    d01_uv_unwrap.sukima_logo_uv_unwrap.sukima_logo_uv_unwrap()
    # --------------------------------
    # Material & Texture (質感, 色)
    # --------------------------------
    d02_mtal.sukima_logo_mtal.sukima_logo_mtal()
    # --------------------------------
    # Bake (マテリアル書き出し)
    # --------------------------------
    d03_bake.sukima_logo_bake.sukima_logo_bake()

    # --------------------------------
    # オブジェクト複製 (Animation用)
    # --------------------------------
    d00_mdl.sukima_logo_mdl.sukima_logo_duplicate()

    # --------------------------------
    # Armature (リギング,ボーン設定,アーマチュア)
    # --------------------------------
    d04_bone.sukima_logo_bone.sukima_logo_bone()
    # --------------------------------
    # Animation (ボーン,トランスフォーム)
    # --------------------------------
    d05_animation.sukima_logo_animation.sukima_logo_animation()
    # --------------------------------
    # Shape Key (メッシュパターン作成)
    # --------------------------------
    d06_shape_key.sukima_logo_shape_key.sukima_logo_shape_key()

