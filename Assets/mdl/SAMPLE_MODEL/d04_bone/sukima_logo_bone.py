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

# ==================================================================
# = Bone
# ==================================================================
def sukima_logo_bone(
    sukima_logo=glb.glb_defs.sukima_logo
,   sukima_logo_bone=glb.glb_defs.sukima_logo_bone
):
    obj_name=sukima_logo
    obj_bone_name=sukima_logo_bone
    # ビューへ切り替え
    mdl_cm_lib.change_preview(key="SOLID")
    # Mode切り替え
    bpy.ops.object.mode_set(mode='OBJECT')
    #----------------------------------
    # 前処理
    #----------------------------------
    # モデリング調整 (Tポーズ)
    ## モディファイア適用
    ## オブジェクト結合
    # ----------------------------------
    # ボーン設定 (リギング)
    # ----------------------------------
    flg = False  # ボーン処理切り替え用 (どちらか選択)
    if (flg):
        # ----------------------------------
        # 手動 ボーン設定 (リギング)
        # ----------------------------------
        if (mm_cm_lib.glb_exist_obj_chk(obj_list=[obj_bone_name], EXIST_FLAG_DICT=glb.glb_defs.EXIST_FLAG_DICT, gen_flag=True)):
            # ボーン 追加
            bpy.ops.object.armature_add(
                enter_editmode=False
            ,   align='WORLD'
            ,   location=(0, 0, 0)
            ,   scale=(1, 1, 1)
            )
            # 名前設定
            bpy.context.object.name = obj_bone_name
            # サイズ変更
            bpy.ops.transform.resize(
                value=(
                    glb.glb_defs.GP_CUBE_SIZE*2/3
                ,   glb.glb_defs.GP_CUBE_SIZE*2/3
                ,   glb.glb_defs.GP_CUBE_SIZE*2/3
                )
            ,   orient_type='GLOBAL'
            )
            # オブジェクト移動
            bpy.ops.transform.translate(
                value=(
                    0
                ,   0
                ,   -(glb.glb_defs.GP_CUBE_SIZE*2 + glb.glb_defs.GP_CUBE_SIZE/2)
                )
            ,   orient_type='GLOBAL'
            )
            # View Display 設定
            bpy.context.object.show_in_front = True     # 前面表示
            bpy.context.object.data.show_names = True   # Bone名表示
            bpy.context.object.data.use_mirror_x = True # 左右対称化

            # アクティブオブジェクト
            ani_cm_lib.active_object_select_ext(
                object_name_list=[obj_bone_name]
            )
            # Mode切り替え
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')
            #----------------------------------
            # Bone 押し出し 胴体 頭
            #----------------------------------
            z_l=[
                +(glb.glb_defs.GP_CUBE_SIZE*2.5/3)
            ,   +(glb.glb_defs.GP_CUBE_SIZE*1.5/3)
            ,   +(glb.glb_defs.GP_CUBE_SIZE*2.7/3)
            ]
            b_l=[
                "Bone"
            ,   "Bone.001"
            ,   "Bone.002"
            ]
            for i in range(len(z_l)):
                # Bone 押し出し
                ani_cm_lib.extrude_edit_bone(
                    armature_obj=obj_bone_name
                ,   bone_name=b_l[i]
                ,   extrude_vec=(0, 0, z_l[i])
                ,   select_part="TAIL"
                ,   symmetric=False
                )
            #----------------------------------
            # Bone 押し出し 腕
            #----------------------------------
            x_l=[
                +(glb.glb_defs.GP_CUBE_SIZE/2)
            ,   +(glb.glb_defs.GP_CUBE_SIZE*2/3)
            ,   +(glb.glb_defs.GP_CUBE_SIZE*4/3)
            ]
            y_l=[
                +0
            ,   +0
            ,   +0
            ]
            z_l=[
                +0
            ,   -(glb.glb_defs.GP_CUBE_SIZE/16)
            ,   -(glb.glb_defs.GP_CUBE_SIZE/16)
            ]
            b_l=[
                "Bone.001"
            ,   "Bone.001_L"
            ,   "Bone.001_L.001"
            ]
            p_l=[
                "TAIL"
            ,   "TAIL"
            ,   "TAIL"
            ]
            for i in range(len(z_l)):
                # 値を取得（lambdaなら実行）
                x_value = x_l[i]() if callable(x_l[i]) else x_l[i]
                y_value = y_l[i]() if callable(y_l[i]) else y_l[i]
                z_value = z_l[i]() if callable(z_l[i]) else z_l[i]
                # Bone 左右対称 押し出し
                ani_cm_lib.extrude_edit_bone(
                    armature_obj=obj_bone_name
                ,   bone_name=b_l[i]
                ,   extrude_vec=(x_value, y_value, z_value)
                ,   select_part=p_l[i]
                ,   symmetric=True
                )
            #----------------------------------
            # Bone 押し出し 脚 足
            #----------------------------------
            x_l=[
                +(glb.glb_defs.GP_CUBE_SIZE/3)
            ,   +0
            ,   +0
            ]
            y_l=[
                +0
            ,   +0
            ,   +0
            ]
            z_l=[
                -(glb.glb_defs.GP_CUBE_SIZE/10)
            ,   -(glb.glb_defs.GP_CUBE_SIZE*1.50)
            ,   -(glb.glb_defs.GP_CUBE_SIZE*1.50)
            ]
            b_l=[
                "Bone"
            ,   "Bone_L"
            ,   "Bone_L.001"
            ]
            p_l=[
                "HEAD"
            ,   "TAIL"
            ,   "TAIL"
            ]
            for i in range(len(z_l)):
                # 値を取得（lambdaなら実行）
                x_value = x_l[i]() if callable(x_l[i]) else x_l[i]
                y_value = y_l[i]() if callable(y_l[i]) else y_l[i]
                z_value = z_l[i]() if callable(z_l[i]) else z_l[i]
                # Bone 左右対称 押し出し
                ani_cm_lib.extrude_edit_bone(
                    armature_obj=obj_bone_name
                ,   bone_name=b_l[i]
                ,   extrude_vec=(x_value, y_value, z_value)
                ,   select_part=p_l[i]
                ,   symmetric=True
                )
        #----------------------------------
        # Bone Mesh 関連付け ペアレント
        #----------------------------------
        # Mode切り替え
        bpy.ops.object.mode_set(mode='OBJECT')
        # アクティブオブジェクト
        ani_cm_lib.active_object_select_ext(
            object_name_list=[obj_name, obj_bone_name]
        )
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        #----------------------------------
        # Bone Weight 調整
        #----------------------------------
        # アクティブオブジェクト
        ani_cm_lib.active_object_select_ext(
            object_name_list=[obj_name]
        )
        # 切り替え
        bpy.ops.paint.weight_paint_toggle()

        # # Weigh 設定 : 頂点
        # ani_cm_lib.set_vertex_group_weight(
        #     obj_name=obj_name
        # ,   group_name="Bone_R.001"
        # ,   vertex_indices=[789]
        # ,   weight=0.0
        # ,   mode="REPLACE"
        # )
        # # Weigh 設定 : 線形
        # ani_cm_lib.weight_gradient_along_bone_connected_only(
        #     obj_name=obj_name
        # ,   bone_name="Bone.001_L.002"
        # ,   start_weight=1.0
        # ,   end_weight=1.0
        # ,   radius=1.0
        # )

        # Bone 選択
        ani_cm_lib.select_bone_in_weightpaint(
            obj_name=obj_name
        ,   bone_name="Bone.001_L.002"
        )
        # 解除
        bpy.ops.paint.weight_paint_toggle()

        #----------------------------------
        # Bone 名前 変更
        #----------------------------------
        # アクティブオブジェクト
        ani_cm_lib.active_object_select_ext(
            object_name_list=[obj_bone_name]
        )
        # Mode切り替え
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        b_l=[
            ["Bone_L.001", "UpperLeg_L"]
        ,   ["Bone_R.001", "UpperLeg_R"]
        ,   ["Bone_L.002", "LowerLeg_L"]
        ,   ["Bone_R.002", "LowerLeg_R"]
        ,   ["Bone_L", "Hip_L"]
        ,   ["Bone_R", "Hip_R"]
        ,   ["Bone", "Spine1"]
        ,   ["Bone.001", "Spine2"]
        ,   ["Bone.002", "Spine3"]
        ,   ["Bone.003", "Spine4"]
        ,   ["Bone.001_L", "Shoulder_L"]
        ,   ["Bone.001_R", "Shoulder_R"]
        ,   ["Bone.001_L.001", "UpperArm_L"]
        ,   ["Bone.001_R.001", "UpperArm_R"]
        ,   ["Bone.001_L.002", "LowerArm_L"]
        ,   ["Bone.001_R.002", "LowerArm_R"]
        ]
        for i in range(len(b_l)):
            # Bone 選択
            ani_cm_lib.select_edit_bone_head_tail(
                armature_obj=obj_bone_name
            ,   bone_name_list=[b_l[i][0]]
            ,   select_part="Head"
            )
            bpy.context.active_bone.name = b_l[i][1]
        #----------------------------------
        # Master Bone 設定
        #----------------------------------
        bpy.context.object.data.use_mirror_x = False # 左右対称化
        x_l=[
            +0
        ]
        y_l=[
            +glb.glb_defs.GP_CUBE_SIZE
        ]
        z_l=[
            +0
        ]
        b_l=[
            "Spine1"
        ]
        p_l=[
            "TAIL"
        ]
        for i in range(len(z_l)):
            # 値を取得（lambdaなら実行）
            x_value = x_l[i]() if callable(x_l[i]) else x_l[i]
            y_value = y_l[i]() if callable(y_l[i]) else y_l[i]
            z_value = z_l[i]() if callable(z_l[i]) else z_l[i]
            # Bone 左右対称 押し出し
            ani_cm_lib.extrude_edit_bone(
                armature_obj=obj_bone_name
            ,   bone_name=b_l[i]
            ,   extrude_vec=(x_value, y_value, z_value)
            ,   select_part=p_l[i]
            ,   symmetric=True
            )
        # アクティブオブジェクト
        ani_cm_lib.active_object_select_ext(
            object_name_list=[obj_bone_name]
        )
        # Mode切り替え
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        b_l=[
            ["Spine1.001", "Master"]
        ]
        for i in range(len(b_l)):
            # Bone 選択
            ani_cm_lib.select_edit_bone_head_tail(
                armature_obj=obj_bone_name
            ,   bone_name_list=[b_l[i][0]]
            ,   select_part="Head"
            )
            bpy.context.active_bone.name = b_l[i][1]
        # Master 親子関係解除
        bpy.context.active_bone.parent = None
        # Bone Parent 設定
        ani_cm_lib.set_bone_parent(
            armature_name=obj_bone_name
        ,   child_bone_name="Spine1"
        ,   parent_bone_name="Master"
        ,   use_connect=False
        )
    else:
        #----------------------------------
        # Rigify ボーン設定 (リギング)
        #----------------------------------
        if (mm_cm_lib.glb_exist_obj_chk(obj_list=[obj_bone_name], EXIST_FLAG_DICT=glb.glb_defs.EXIST_FLAG_DICT, gen_flag=True)):
            # Addon 有効化: Rigify 
            mm_cm_lib.enable_add_on(addon_name="rigify")
            # ボーン 追加
            bpy.ops.object.armature_basic_human_metarig_add()
            # 名前設定
            bpy.context.object.name = obj_bone_name
            # サイズ変更
            bpy.ops.transform.resize(
                value=(
                    0.875
                ,   0.875
                ,   0.875
                )
            ,   orient_type='GLOBAL'
            )
            # オブジェクト移動
            bpy.ops.transform.translate(
                value=(
                    0
                ,   0
                ,   -(glb.glb_defs.GP_CUBE_SIZE*5 + glb.glb_defs.GP_CUBE_SIZE/2 + (glb.glb_defs.GP_CUBE_SIZE/10))
                )
            ,   orient_type='GLOBAL'
            )
            # View Display 設定
            bpy.context.object.show_in_front = True     # 前面表示
            bpy.context.object.data.show_names = True   # Bone名表示
            bpy.context.object.data.use_mirror_x = True # 左右対称化
            # アクティブオブジェクト
            ani_cm_lib.active_object_select_ext(
                object_name_list=[obj_bone_name]
            )
            # Mode切り替え
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')
            # Bone 変形
            b_l=[
                "thigh.L"
            ,   "hand.L"
            ,   "hand.L"
            ,   "forearm.L"
            ]
            p_l=[
                "HEAD"
            ,   "TAIL"
            ,   "HEAD"
            ,   "HEAD"
            ]
            x_l=[
                0
            ,   +(glb.glb_defs.GP_CUBE_SIZE/3)
            ,   +(glb.glb_defs.GP_CUBE_SIZE/3)
            ,   +(glb.glb_defs.GP_CUBE_SIZE/4)
            ]
            y_l=[
                0
            ,   0
            ,   0
            ,   0
            ]
            z_l=[
                -(glb.glb_defs.GP_CUBE_SIZE/10)
            ,   +(glb.glb_defs.GP_CUBE_SIZE*7/10)
            ,   +(glb.glb_defs.GP_CUBE_SIZE*6/10)
            ,   +(glb.glb_defs.GP_CUBE_SIZE*2/10)
            ]
            for i in range(len(b_l)):
                # Bone 選択
                ani_cm_lib.select_edit_bone_head_tail(
                    armature_obj=obj_bone_name
                ,   bone_name_list=[b_l[i]]
                ,   select_part=p_l[i]
                )
                # 値を取得（lambdaなら実行）
                x_value = x_l[i]() if callable(x_l[i]) else x_l[i]
                y_value = y_l[i]() if callable(y_l[i]) else y_l[i]
                z_value = z_l[i]() if callable(z_l[i]) else z_l[i]    
                # 移動
                bpy.ops.transform.translate(
                    value=(x_value, y_value, z_value)
                ,   orient_type='GLOBAL'
                )
        #----------------------------------
        # Bone Mesh 関連付け ペアレント
        #----------------------------------
        # Mode切り替え
        bpy.ops.object.mode_set(mode='OBJECT')
        # アクティブオブジェクト
        ani_cm_lib.active_object_select_ext(
            object_name_list=[obj_name, obj_bone_name]
        )
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        #----------------------------------
        # Bone Weight 調整
        #----------------------------------
        # アクティブオブジェクト
        ani_cm_lib.active_object_select_ext(
            object_name_list=[obj_name]
        )
        # 切り替え
        bpy.ops.paint.weight_paint_toggle()

        # # Weigh 設定 : 頂点
        # ani_cm_lib.set_vertex_group_weight(
        #     obj_name=obj_name
        # ,   group_name="Bone_R.001"
        # ,   vertex_indices=[789]
        # ,   weight=0.0
        # ,   mode="REPLACE"
        # )
        # # Weigh 設定 : 線形
        # ani_cm_lib.weight_gradient_along_bone_connected_only(
        #     obj_name=obj_name
        # ,   bone_name="Bone.001_L.002"
        # ,   start_weight=1.0
        # ,   end_weight=1.0
        # ,   radius=1.0
        # )

        # Bone 選択
        ani_cm_lib.select_bone_in_weightpaint(
            obj_name=obj_name
        ,   bone_name="spine.006"
        )

        # 解除
        bpy.ops.paint.weight_paint_toggle()

