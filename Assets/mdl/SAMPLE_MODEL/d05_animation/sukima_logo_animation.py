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
modules = common_top.import_submodules(f"Assets.mdl.SAMPLE_MODEL") 
parts = common_top.import_submodules("Assets.parts")

globals().update(modules)
globals().update(parts)

# ==================================================================
# = Animation
# ==================================================================
def sukima_logo_animation(
    sukima_logo=glb.glb_defs.sukima_logo
,   sukima_logo_bone=glb.glb_defs.sukima_logo_bone
):
    if (mm_cm_lib.glb_exist_obj_chk(obj_list=[sukima_logo_bone], EXIST_FLAG_DICT=glb.glb_defs.EXIST_FLAG_DICT)):
        obj_name=sukima_logo
        obj_bone_name=sukima_logo_bone
        # Mode切り替え
        bpy.ops.object.mode_set(mode='OBJECT')
        # Animation 設定
        bpy.context.scene.sync_mode = 'AUDIO_SYNC'
        # 現在のシーンを取得
        scene = bpy.context.scene
        # フレームレートを設定（例：30fps）
        scene.render.fps = 30
        # アクティブオブジェクト
        ani_cm_lib.active_object_select_ext(
            object_name_list=[obj_bone_name]
        )
        # ポーズモード切替
        bpy.ops.object.posemode_toggle()
        # --------------------------------
        # キーフレーム
        # --------------------------------
        b_l=[
            ["shin.L", "thigh.L"]   # 左足
        ,   ["shin.R", "thigh.R"]   # 右足
        ]
        m_l=[
            0
        ,   7
        ]
        for j in range(len(b_l)):
            bone_name=b_l[j][0]
            f_l=[
                1   + m_l[j]
            ,   10  + m_l[j]
            ]
            d_l=[
                "rotation_euler"
            ,   "rotation_euler"
            ]
            v_l=[
                None
            ,   (math.radians(+80), 0, 0)
            ]
            for i in range(len(f_l)):
                # キーフレーム
                ani_cm_lib.insert_pose_bone_keyframe(
                    armature_name=sukima_logo_bone
                ,   bone_name=bone_name
                ,   frame=f_l[i]
                ,   data_path=d_l[i]
                ,   value=v_l[i]
                )
            # キーフレーム 選択
            ani_cm_lib.select_pose_bone_keyframes(
                armature_name=sukima_logo_bone
            ,   bone_name=bone_name
            ,   data_path="rotation_euler"
            ,   frame_list=f_l
            ,   axis=None
            )
            for i in range(5):
                # キーフレーム複製
                ani_cm_lib.duplicate_selected_keyframes(
                    armature_name=sukima_logo_bone
                ,   offset_frames=18
                )
            bone_name=b_l[j][1]
            f_l=[
                1   + m_l[j]
            ,   10  + m_l[j]
            ]
            d_l=[
                "rotation_euler"
            ,   "rotation_euler"
            ]
            v_l=[
                (math.radians(-50), 0, 0)
            ,   (math.radians(+30), 0, 0)
            ]
            for i in range(len(f_l)):
                # キーフレーム
                ani_cm_lib.insert_pose_bone_keyframe(
                    armature_name=sukima_logo_bone
                ,   bone_name=bone_name
                ,   frame=f_l[i]
                ,   data_path=d_l[i]
                ,   value=v_l[i]
                )
            # キーフレーム 選択
            ani_cm_lib.select_pose_bone_keyframes(
                armature_name=sukima_logo_bone
            ,   bone_name=bone_name
            ,   data_path="rotation_euler"
            ,   frame_list=f_l
            ,   axis=None
            )
            for i in range(5):
                # キーフレーム複製
                ani_cm_lib.duplicate_selected_keyframes(
                    armature_name=sukima_logo_bone
                ,   offset_frames=18
                )
            # キーフレーム 選択
            ani_cm_lib.select_pose_bone_keyframes(
                armature_name=sukima_logo_bone
            ,   bone_name=bone_name
            ,   data_path="rotation_euler"
            ,   frame_list=None
            ,   axis=None
            )
            # キーフレーム 移動
            ani_cm_lib.move_selected_keyframes(
                armature_name=sukima_logo_bone
            ,   offset_frames=-5
            )
        # --------------------------------
        # キーフレーム 登録
        # --------------------------------
        # アクション モード変更
        ani_cm_lib.set_dopesheet_mode_to_action()
        # Action Name 変更
        ani_cm_lib.rename_current_armature_action(
            armature_name=sukima_logo_bone
        ,   new_action_name=glb.glb_defs.ANI_SUKIMA_LOGO_BONE_RUN
        )
        # フレーム長 調整
        bpy.data.actions[glb.glb_defs.ANI_SUKIMA_LOGO_BONE_RUN].use_frame_range = True
        frame_start_key = 18
        frame_end_key   = 90
        bpy.data.actions[glb.glb_defs.ANI_SUKIMA_LOGO_BONE_RUN].frame_start  = frame_start_key
        bpy.data.actions[glb.glb_defs.ANI_SUKIMA_LOGO_BONE_RUN].frame_end    = frame_end_key
        # ループアニメーション
        bpy.data.actions[glb.glb_defs.ANI_SUKIMA_LOGO_BONE_RUN].use_cyclic = True
        # Animation 登録: ストリップ化
        ani_cm_lib.safe_push_down(
            obj_name=sukima_logo_bone
        ,   track_name=glb.glb_defs.ANI_SUKIMA_LOGO_BONE_RUN
        )
        # NLA設定
        ani_cm_lib.set_nla_strip_properties(
            obj_name=sukima_logo_bone
        ,   strip_name=glb.glb_defs.ANI_SUKIMA_LOGO_BONE_RUN
        ,   frame_start_ui=0
        ,   frame_end_ui=(frame_end_key - frame_start_key)  # Length = (frame_end_ui) * repeat
        ,   repeat=4
        ,   blend_type='ADD'
        ,   mute=False
        ,   scale=1.0
        ,   use_reverse=False                               # 反転
        ,   use_animated_influence=False
        ,   influence=1.0
        )
